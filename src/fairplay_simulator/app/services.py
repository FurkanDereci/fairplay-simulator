"""Orkestrasyon katmanı — iş mantığı **tek yerde**.

Kurallar:
- Router yalnız parse → servis → serialize yapar; burada olmayan bir hesabı orada yapmaz.
- **Sunucu otoritedir:** settlement sonucu istemciden değil, maç motorundan gelir.
- Para alanları API'de **string** olarak döner (JSON'da tam hassasiyet korunur).
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Mapping, Sequence
from datetime import datetime
from decimal import Decimal

from ..core import energy as energy_mod
from ..core.cooldown import MAX_COOLDOWN_HOURS, SOLVENT_DAYS_PER_TIER, CooldownState
from ..core.errors import InsufficientCash, InvalidAmount
from ..core.learning import (
    DISCOUNTED_MAX_COOLDOWN_HOURS,
    FAVOURITE_LINE,
    MIN_SAMPLE,
    STAKE_RATIO_LIMIT,
    BetInput,
    build_learning_report,
    earned_badges,
    earns_discipline_discount,
)
from ..core.ledger import EntryType, LedgerEntry
from ..core.metrics import (
    MIN_T_STATISTIC,
    beta_alpha,
    is_statistically_reliable,
    max_drawdown_pct,
    returns_series,
    risk_adjusted_score,
    sharpe,
    sharpe_t_statistic,
    sortino,
    trade_stats,
)
from ..core.money import BASE_NAV, ONE, ZERO, Money, dec, q, q_money, q_nav, to_pct
from ..core.nav import Fund, nav_series, settled_outcomes
from ..core.odds import (
    NormalizedMarket,
    clv_pct,
    expected_value,
    kelly_fraction,
    risk_of_ruin,
    validate_market_odds,
)
from ..engines.bots import BotStrategy, benchmark_series
from ..engines.match import (
    MARKET_1X2,
    MatchRecord,
    derive_lambdas,
    run_monte_carlo,
    simulate_match,
)
from ..repo import Repository, UserRecord, WagerRecord
from . import fixtures as fixture_catalog
from .clock import Clock
from .config import Settings
from .errors import (
    Conflict,
    EnergyDepleted,
    LockedOut,
    NotFound,
    RuinConfirmationRequired,
    Unauthorized,
    UnknownFixture,
    UnknownMarket,
)
from .fixtures import Fixture
from .security import create_token, decode_token, hash_password, verify_password

REFILL_AMOUNT: Money = Decimal("1000")
INITIAL_DEPOSIT: Money = Decimal("1000")


def _settlement_status(stake: Money, payout: Money | None) -> str:
    """Kuponun görünüm durumu; ödeme tutarından türetilir (ayrı durum kolonu yok)."""
    if payout is None:
        return "PENDING"
    if payout > stake:
        return "WON"
    if payout == stake:
        return "VOID"
    if payout == ZERO:
        return "LOST"
    return "PARTIAL"


class PortfolioService:
    def __init__(self, repo: Repository, settings: Settings, clock: Clock) -> None:
        self.repo = repo
        self.settings = settings
        self.clock = clock

    # --- kimlik -----------------------------------------------------------------
    def register(self, *, username: str, email: str, password: str) -> tuple[UserRecord, str]:
        if self.repo.user_by_username(username) is not None:
            raise Conflict("Bu kullanıcı adı alınmış.")
        user = self.repo.create_user(username, email, hash_password(password))
        # Fon defteri başlangıç yatırımıyla açılır: 1000 TL @ NAV 100 → 10 birim.
        self.repo.append_entry(
            user.id, LedgerEntry(seq=0, entry_type=EntryType.DEPOSIT, amount=INITIAL_DEPOSIT)
        )
        self.repo.save_energy(user.id, self.settings.energy_max, self.clock.now())
        self.repo.save_cooldown(user.id, CooldownState())
        return user, self._token(user)

    def login(self, *, username: str, password: str) -> tuple[UserRecord, str]:
        user = self.repo.user_by_username(username)
        if user is None or not verify_password(password, user.password_hash):
            raise Unauthorized("Kullanıcı adı veya parola hatalı.")
        return user, self._token(user)

    def user_from_token(self, token: str) -> UserRecord:
        payload = decode_token(token, self.settings.jwt_secret, now=self.clock.now())
        subject = payload.get("sub") if payload else None
        if not isinstance(subject, str):
            raise Unauthorized("Geçersiz veya süresi dolmuş token.")
        user = self.repo.user_by_id(subject)
        if user is None:
            raise Unauthorized("Token bir kullanıcıya çözülemedi.")
        return user

    def _token(self, user: UserRecord) -> str:
        return create_token(
            user_id=user.id,
            username=user.username,
            secret=self.settings.jwt_secret,
            ttl_minutes=self.settings.jwt_ttl_minutes,
            now=self.clock.now(),
        )

    # --- durum okuma -------------------------------------------------------------
    def _require_user(self, user_id: str) -> UserRecord:
        user = self.repo.user_by_id(user_id)
        if user is None:
            raise NotFound("Kullanıcı bulunamadı.")
        return user

    def _fund(self, user_id: str) -> tuple[Fund, list[LedgerEntry]]:
        entries = self.repo.entries(user_id)
        return Fund.replay(entries), entries

    def _energy(self, user_id: str) -> tuple[int, datetime]:
        now = self.clock.now()
        state = self.repo.energy(user_id)
        if state is None:
            return self.settings.energy_max, now
        energy, last_update = energy_mod.regen(
            state[0],
            state[1],
            now,
            max_energy=self.settings.energy_max,
            per_hour=Decimal(self.settings.energy_per_hour),
        )
        return energy, last_update

    def _cooldown(self, user_id: str) -> CooldownState:
        state = self.repo.cooldown(user_id)
        if state.unlock_if_expired(self.clock.now()):
            self.repo.save_cooldown(user_id, state)
        return state

    def _cooldown_with_solvent_days(self, user_id: str, fund: Fund) -> CooldownState:
        """Duvar saati gün sınırını işler ve cooldown durumunu döner (spec §4.2).

        Gün sınırı yalnız **etkileşim anında** gözlenir: her çağrı bir "tick"tir. Hesap solventse
        geçen günler birikir (3 gün → tier bir kademe düşer); iflastaysa geçen günler **yanar**
        (ileriye taşınmaz) — bu, sayacın iyi niyetli bir ölçümü olduğunun sınırıdır.
        """
        state = self._cooldown(user_id)
        state.accrue_solvent_days(self.clock.now().date(), solvent=fund.total_value > ZERO)
        self.repo.save_cooldown(user_id, state)
        return state

    def _bet_inputs(self, user_id: str) -> dict[str, BetInput]:
        """Öğrenme ölçütlerinin girdisi: kupon metadata'sı (DB tipi çekirdeğe sızmaz)."""
        return {
            record.wager_id: BetInput(
                wager_id=record.wager_id,
                market_type=record.market_type,
                odds=record.odds,
                closing_odds=record.closing_odds,
            )
            for record in self.repo.wagers_for(user_id)
        }

    def _badges(self, user_id: str) -> tuple[str, ...]:
        """Kullanıcının kazandığı disiplin rozetleri (spec §4.2)."""
        report = build_learning_report(self.repo.entries(user_id), self._bet_inputs(user_id))
        return earned_badges(report)

    def _cooldown_cap_hours(self, badges: Sequence[str]) -> Money:
        """Rozet sayısına göre cooldown tavanı: üç rozet → 72 saat, yoksa 168 (spec §4.2)."""
        return (
            DISCOUNTED_MAX_COOLDOWN_HOURS
            if earns_discipline_discount(badges)
            else MAX_COOLDOWN_HOURS
        )

    def _market_selection(
        self, match_id: str, market_type: str, selection: str
    ) -> tuple[Fixture, NormalizedMarket, Money]:
        """Maç + market + seçim çözümü **tek yerde**; bilinmeyen hiçbir şey sessizce varsayılmaz."""
        fixture = fixture_catalog.get(match_id)
        if fixture is None:
            raise UnknownFixture(f"Bilinmeyen maç: {match_id}")
        market = fixture.markets.get(market_type)
        if market is None:
            raise UnknownMarket(f"Bilinmeyen market: {market_type}")
        odds = market.outcomes.get(selection)
        if odds is None:
            raise UnknownMarket(f"Bilinmeyen seçim: {selection}")
        return fixture, market, odds

    # --- değerlendirme (kullanıcı olasılığı) ---------------------------------------
    def estimate(
        self,
        *,
        user_id: str,
        match_id: str,
        market_type: str,
        selection: str,
        probability: Money,
    ) -> dict[str, object]:
        """Kullanıcının **kendi olasılık tahmininden** EV ve Kelly üretir.

        Piyasanın fair olasılığı `p` olarak kullanılsaydı `f*` her zaman 0 çıkardı; bu yüzden
        `p` dışarıdan gelir (bkz. ADR-0006).
        """
        self._require_user(user_id)
        _fixture, market, odds = self._market_selection(match_id, market_type, selection)
        fund, _ = self._fund(user_id)
        return self._assessment(market, selection, odds, probability, fund.cash)

    def _assessment(
        self,
        market: NormalizedMarket,
        selection: str,
        odds: Money,
        probability: Money,
        cash: Money,
    ) -> dict[str, object]:
        fair_prob = market.fair_prob.get(selection, ZERO)
        fair_odds = market.fair_odds.get(selection, ZERO)
        ev = expected_value(probability, odds)
        kelly = kelly_fraction(probability, odds)
        positive = ev > ZERO

        return {
            "odds": str(odds),
            "fair_odds": str(fair_odds),
            "fair_prob": str(fair_prob),
            "probability": str(q(probability, Decimal("0.0001"))),
            "edge_pct": str(to_pct(probability - fair_prob)),
            "ev": str(q(ev, Decimal("0.0001"))),
            "ev_pct": str(to_pct(ev)),
            "kelly_fraction": str(q(kelly, Decimal("0.0001"))),
            "suggested_stake": str(q_money(kelly * cash)),
            "verdict": "POZITIF" if positive else "NEGATIF",
            "note": (
                "Tahminin piyasanın fair olasılığından yüksek: pozitif EV."
                if positive
                else "Bu oranla pozitif EV yok; Kelly stake önermiyor (%0)."
            ),
        }

    # --- para hareketleri ---------------------------------------------------------
    def place_wager(
        self,
        *,
        user_id: str,
        match_id: str,
        market_type: str,
        selection: str,
        stake: Money,
        probability: Money | None = None,
        confirm_ruin: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, object]:
        if idempotency_key is not None:
            cached = self.repo.idempotent_response(user_id, idempotency_key)
            if cached is not None:
                restored: dict[str, object] = json.loads(cached)
                return restored

        payload = self._place_wager(
            user_id=user_id,
            match_id=match_id,
            market_type=market_type,
            selection=selection,
            stake=stake,
            probability=probability,
            confirm_ruin=confirm_ruin,
        )
        if idempotency_key is not None:
            self.repo.save_idempotent_response(
                user_id, idempotency_key, json.dumps(payload, ensure_ascii=False)
            )
        return payload

    def _ruin_payload(
        self,
        stake: Money,
        cash_before: Money,
        odds: Money,
        probability: Money | None,
    ) -> dict[str, object]:
        """Ruin uyarısının **yapısal** gövdesi (modal bunu gösterir).

        `p` verilmezse `R_ruin` sayısı **uydurulmaz** (`null`); kullanıcı tahminini girerse
        hesaplanır (ADR-0006, spec §3.4).
        """
        payload: dict[str, object] = {
            "stake": str(q_money(stake)),
            "cash": str(q_money(cash_before)),
            "pct_of_cash": str(to_pct(stake / cash_before)),
            "threshold_pct": str(to_pct(dec(self.settings.risk_of_ruin_threshold))),
            "risk_of_ruin_pct": None,
            "message": (
                "Bu stake kasanın %15 eşiğini aşıyor: iflas riski yüksek. "
                "Onay verirsen bahis işlenecek."
            ),
        }
        if probability is not None:
            edge = expected_value(probability, odds)
            payload["edge"] = str(q(edge, Decimal("0.0001")))
            payload["units"] = str(q(cash_before / stake, Decimal("0.0001")))
            payload["risk_of_ruin_pct"] = str(risk_of_ruin(edge, cash_before / stake))
        return payload

    def _place_wager(
        self,
        *,
        user_id: str,
        match_id: str,
        market_type: str,
        selection: str,
        stake: Money,
        probability: Money | None = None,
        confirm_ruin: bool = False,
    ) -> dict[str, object]:
        self._require_user(user_id)
        now = self.clock.now()

        # Sıra bilinçli: reddedilecek bir istek **hiçbir yan etki** bırakmaz. Önce bütün
        # doğrulamalar ve ruin kapısı, en sonda enerji harcaması ve defter kaydı yapılır.
        # Defter okuması yan etkisizdir; solvent-gün tick'i için kilit denetiminden önce alınır.
        fund, _ = self._fund(user_id)
        cooldown = self._cooldown_with_solvent_days(user_id, fund)
        if cooldown.is_locked(now):
            raise LockedOut(f"Hesap iflas cooldown'ında (tier {cooldown.tier}).")

        fixture, market, odds = self._market_selection(match_id, market_type, selection)

        if stake <= ZERO:
            raise InvalidAmount("Bahis tutarı pozitif olmalı.")
        if stake > fund.cash:
            raise InsufficientCash("Kasa bu bahsi karşılayamaz.")
        cash_before = fund.cash

        threshold = dec(self.settings.risk_of_ruin_threshold)
        ruin = stake > threshold * cash_before
        if ruin and not confirm_ruin:
            raise RuinConfirmationRequired(
                "Bu stake kasanın %15 eşiğini aşıyor: onay ister (spec §3.4).",
                self._ruin_payload(stake, cash_before, odds, probability),
            )

        energy, last_update = self._energy(user_id)
        if not energy_mod.can_wager(energy, cost=self.settings.energy_per_wager):
            raise EnergyDepleted(
                f"Simülasyon enerjisi yetersiz ({energy}/{self.settings.energy_max}). "
                f"Her bahis {self.settings.energy_per_wager} enerji harcar."
            )
        energy = energy_mod.spend(energy, cost=self.settings.energy_per_wager)
        self.repo.save_energy(user_id, energy, last_update)

        wager_id = str(uuid.uuid4())
        self.repo.save_wager(
            wager_id=wager_id,
            user_id=user_id,
            match_id=match_id,
            match_title=fixture.title,
            market_type=market_type,
            selection=selection,
            odds=odds,
        )
        entry = LedgerEntry(
            seq=0, entry_type=EntryType.WAGER_PLACED, amount=stake, wager_id=wager_id
        )
        self.repo.append_entry(user_id, entry)
        fund.apply(entry)

        risk_of_ruin_pct: str | None = None
        if ruin and probability is not None:
            edge = expected_value(probability, odds)
            risk_of_ruin_pct = str(risk_of_ruin(edge, cash_before / stake))
        return {
            "wager_id": wager_id,
            "match_id": match_id,
            "match_title": fixture.title,
            "market_type": market_type,
            "selection": selection,
            "stake": str(q_money(stake)),
            "odds": str(odds),
            "potential_payout": str(q_money(stake * odds)),
            "fair_odds": str(market.fair_odds.get(selection, ZERO)),
            "cash_balance": str(q_money(fund.cash)),
            "nav": str(q_nav(fund.nav)),
            "simulation_energy": energy,
            "ruin_risk_warning": ruin,
            "risk_of_ruin_pct": risk_of_ruin_pct,
            "warning_message": (
                "Stake kasasının %15'ini aşıyor: portföyü iflasa sürükleme olasılığı yüksek."
                if ruin
                else None
            ),
            "assessment": (
                self._assessment(market, selection, odds, probability, cash_before)
                if probability is not None
                else None
            ),
        }

    def refill(self, *, user_id: str) -> dict[str, object]:
        self._require_user(user_id)
        cooldown = self._cooldown(user_id)
        if cooldown.is_locked(self.clock.now()):
            raise LockedOut("Cooldown aktifken refill verilmez.")

        entry = LedgerEntry(seq=0, entry_type=EntryType.REFILL, amount=REFILL_AMOUNT)
        self.repo.append_entry(user_id, entry)
        fund, _ = self._fund(user_id)
        return {
            "refilled": str(q_money(REFILL_AMOUNT)),
            "cash_balance": str(q_money(fund.cash)),
            "units": str(fund.units),
            "nav": str(q_nav(fund.nav)),
            "series_id": fund.series_id,
            "twr_pct": str(fund.twr),
        }

    # --- sunucu-otoriteli settlement ------------------------------------------------
    def simulate_match(
        self, *, user_id: str, match_id: str, seed: int | None = None
    ) -> dict[str, object]:
        self._require_user(user_id)
        fixture = fixture_catalog.get(match_id)
        if fixture is None:
            raise UnknownFixture(f"Bilinmeyen maç: {match_id}")

        odds_1x2 = fixture.odds_1x2()
        # Bir maç **bir kez** üretilir (Suite 4): kayıt varsa sonuç kayıtlı seed'den yeniden
        # üretilir, yoksa istek işlenip kaydedilir. Böylece tekrarlanan çağrı aynı skoru/olayları
        # verir, ikinci kez ödeme yapılmaz ve yanıt depoyla çelişmez.
        existing = self.repo.match(match_id)
        if existing is not None:
            odds_1x2 = dict(existing.odds_1x2)
            result = simulate_match(
                match_id, existing.home_team, existing.away_team, odds_1x2, seed=existing.seed
            )
        else:
            result = simulate_match(
                match_id, fixture.home_team, fixture.away_team, odds_1x2, seed=seed
            )
            self.repo.save_match(
                MatchRecord(
                    match_id=match_id,
                    home_team=fixture.home_team,
                    away_team=fixture.away_team,
                    home_score=result.home_score,
                    away_score=result.away_score,
                    odds_1x2=odds_1x2,
                    seed=seed,
                )
            )

        fund, _ = self._fund(user_id)
        settled: list[dict[str, object]] = []
        for record in self.repo.wagers_for(user_id, match_id=match_id):
            stake = fund.open_wagers.get(record.wager_id)
            if stake is None:
                continue
            won = result.outcome_for(record.market_type) == record.selection
            payout = q_money(stake * record.odds) if won else ZERO

            closing = fixture_catalog.closing_odds(
                record.match_id, record.selection, record.odds
            )
            self.repo.set_closing_odds(record.wager_id, closing)

            entry = LedgerEntry(
                seq=0,
                entry_type=EntryType.WAGER_SETTLED,
                amount=payout,
                stake=stake,
                wager_id=record.wager_id,
            )
            self.repo.append_entry(user_id, entry)
            fund.apply(entry)
            settled.append(
                {
                    "wager_id": record.wager_id,
                    "selection": record.selection,
                    "status": "WON" if won else "LOST",
                    "stake": str(q_money(stake)),
                    "payout": str(q_money(payout)),
                    "net": str(q_money(payout - stake)),
                }
            )

        bankruptcy = self._apply_bankruptcy(user_id, fund)
        return {
            "match_id": match_id,
            "match_title": fixture.title,
            "home_team": fixture.home_team,
            "away_team": fixture.away_team,
            "home_score": result.home_score,
            "away_score": result.away_score,
            "score": f"{result.home_score} - {result.away_score}",
            "outcomes": {
                "1X2": result.outcome_1x2,
                "OVER_UNDER_2.5": result.outcome_ou_25,
                "BTTS": result.outcome_btts,
            },
            "events": [
                {
                    "minute": event.minute,
                    "team": event.team,
                    "type": event.event_type,
                    "description": event.description,
                }
                for event in result.events
            ],
            "settled_wagers": settled,
            "cash_balance": str(q_money(fund.cash)),
            "nav": str(q_nav(fund.nav)),
            "bankruptcy_triggered": bankruptcy,
            "twr_pct": str(fund.twr),
        }

    def monte_carlo(
        self,
        *,
        user_id: str,
        match_id: str | None,
        odds_1x2: Mapping[str, Money] | None,
        iterations: int,
        seed: int | None,
    ) -> dict[str, object]:
        """Sonuç dağılımı analizi. Bahis oynatmaz, deftere hiçbir şey yazmaz.

        İki kaynak: `match_id` (katalog oranları) **veya** ham `odds_1x2` (varsayımsal senaryo).
        Aynı `seed` her zaman aynı dağılımı verir.
        """
        self._require_user(user_id)

        if match_id is not None:
            fixture = fixture_catalog.get(match_id)
            if fixture is None:
                raise UnknownFixture(f"Bilinmeyen maç: {match_id}")
            odds: dict[str, Money] = dict(fixture.odds_1x2())
            title: str | None = fixture.title
            source = "CATALOG"
        else:
            odds = dict(odds_1x2 or {})
            if not odds:
                raise UnknownMarket("Oran verilmedi.")
            title = None
            source = "CUSTOM"

        # Bozuk/negatif vig'li besleme burada **reddedilir**, kırpılmaz (Suite 3).
        validate_market_odds(MARKET_1X2, odds)
        lambda_home, lambda_away = derive_lambdas(odds)
        summary = run_monte_carlo(lambda_home, lambda_away, iterations, seed=seed)
        return {
            "source": source,
            "match_id": match_id,
            "match_title": title,
            "odds_1x2": {key: str(value) for key, value in odds.items()},
            "lambda_home": round(lambda_home, 4),
            "lambda_away": round(lambda_away, 4),
            "monte_carlo": {
                "iterations": summary.iterations,
                "home_win_pct": summary.home_win_pct,
                "draw_pct": summary.draw_pct,
                "away_win_pct": summary.away_win_pct,
                "over_25_pct": summary.over_25_pct,
                "btts_pct": summary.btts_pct,
            },
            "seed": seed,
        }

    def _apply_bankruptcy(self, user_id: str, fund: Fund) -> bool:
        """İflas sonrası cooldown'ı **tek** yerden tetikler; tavan rozetlere göre seçilir."""
        if fund.total_value > ZERO:
            return False
        cooldown = self.repo.cooldown(user_id)
        if cooldown.locked_until is not None:
            return False
        cap = self._cooldown_cap_hours(self._badges(user_id))
        cooldown.trigger(self.clock.now(), max_hours=cap)
        self.repo.save_cooldown(user_id, cooldown)
        return True

    # --- görünümler ---------------------------------------------------------------
    def fixtures(self) -> list[dict[str, object]]:
        now = self.clock.now()
        out: list[dict[str, object]] = []
        for fixture in fixture_catalog.all_fixtures():
            out.append(
                {
                    "match_id": fixture.match_id,
                    "league": fixture.league,
                    "home_team": fixture.home_team,
                    "away_team": fixture.away_team,
                    "kickoff_time": fixture_catalog.kickoff(fixture.match_id, now=now).isoformat(),
                    "markets": {
                        market_type: {
                            "outcomes": {k: str(v) for k, v in market.outcomes.items()},
                            "fair_odds": {k: str(v) for k, v in market.fair_odds.items()},
                            "overround": str(market.overround),
                            "margin_pct": str(market.margin_pct),
                        }
                        for market_type, market in fixture.markets.items()
                    },
                }
            )
        return out

    def _nav_at_matches(self, user_id: str, entries: Sequence[LedgerEntry]) -> list[str]:
        """Portföy NAV'ı **maç sınırlarında** — benchmark botlarıyla ortak zaman ekseni için.

        Portföy her defter hareketinde, botlar her maçta örneklenir; ikisini aynı grafiğe koymak
        için portföyü de maç başına örneklemek gerekir. Aksi hâlde seriler farklı eksenlere düşer
        ve karşılaştırma yanıltıcı olur.
        """
        wager_match = {w.wager_id: w.match_id for w in self.repo.wagers_for(user_id)}
        order = [record.match_id for record in self.repo.matches()]

        running = Fund()
        last_nav: dict[str, Money] = {}
        for entry in entries:
            running.apply(entry)
            if entry.entry_type is EntryType.WAGER_SETTLED and entry.wager_id in wager_match:
                last_nav[wager_match[entry.wager_id]] = running.nav

        series: list[Money] = [BASE_NAV]
        for match_id in order:
            series.append(last_nav.get(match_id, series[-1]))
        return [str(q_nav(point)) for point in series]

    def learning_report(self, *, user_id: str) -> dict[str, object]:
        """Öğrenme ölçütleri (docs/90): davranış ölçülür, **tavsiye verilmez**."""
        self._require_user(user_id)
        report = build_learning_report(self.repo.entries(user_id), self._bet_inputs(user_id))
        badges = earned_badges(report)
        return {
            "bets": report.bets,
            "min_sample": MIN_SAMPLE,
            "reliable": report.reliable,
            "market_breadth": report.market_breadth,
            "badges": list(badges),
            "clv": {
                "mean_pct": report.clv_mean_pct,
                "first_half_pct": report.clv_first_half_pct,
                "second_half_pct": report.clv_second_half_pct,
                "trend": report.clv_trend,
            },
            "stake": {
                "mean_ratio_pct": report.mean_stake_ratio_pct,
                "limit_pct": to_pct(STAKE_RATIO_LIMIT),
                "verdict": report.stake_verdict,
            },
            "favourite": {
                "share_pct": report.favourite_share_pct,
                "line": str(FAVOURITE_LINE),
                "verdict": report.favourite_verdict,
            },
            "headline": report.headline,
        }

    def portfolio(self, *, user_id: str) -> dict[str, object]:
        user = self._require_user(user_id)
        fund, entries = self._fund(user_id)
        series = nav_series(entries)
        returns = returns_series(series)

        max_drawdown = max_drawdown_pct(series)
        sharpe_ratio = sharpe(returns)
        sortino_ratio = sortino(returns)
        twr = float(fund.twr)

        records = self.repo.matches()
        bench_series = benchmark_series(records)
        favourite = bench_series[BotStrategy.FAVORITE_HEAVY]
        beta, alpha = beta_alpha(returns, returns_series(favourite))

        stats = trade_stats(settled_outcomes(entries))
        # Anlamlılık kapısı (docs/20 §2.8): yetersiz örneklemde risk metrikleri yorumlanmamalı.
        periods = len(returns)
        t_statistic = sharpe_t_statistic(sharpe_ratio, periods)
        reliable = is_statistically_reliable(t_statistic)
        energy, last_update = self._energy(user_id)
        self.repo.save_energy(user_id, energy, last_update)
        cooldown = self._cooldown_with_solvent_days(user_id, fund)
        badges = self._badges(user_id)
        cap_hours = self._cooldown_cap_hours(badges)

        reliability = {
            "periods": periods,
            "min_t_statistic": MIN_T_STATISTIC,
            "sharpe_t_statistic": t_statistic,
            "sharpe_reliable": reliable,
            "profit_factor_defined": stats.gross_loss > 0,
            "note": (
                ""
                if reliable
                else (
                    "Örneklem yetersiz: Sharpe/Sortino/MDD yorumlanmamalı "
                    f"(t = {t_statistic} < {MIN_T_STATISTIC}, T = {periods})."
                )
            ),
        }

        payouts = {
            entry.wager_id: entry
            for entry in entries
            if entry.entry_type is EntryType.WAGER_SETTLED
        }
        records_by_id = {record.wager_id: record for record in self.repo.wagers_for(user_id)}
        pending: list[dict[str, object]] = []
        settled: list[dict[str, object]] = []
        for wager_id, record in records_by_id.items():
            stake = fund.open_wagers.get(wager_id)
            if stake is not None:
                pending.append(self._wager_view(record, stake, payout=None))
            elif wager_id in payouts:
                settled_entry = payouts[wager_id]
                settled.append(
                    self._wager_view(record, settled_entry.stake, settled_entry.amount)
                )

        return {
            "user": {"id": user.id, "username": user.username},
            "fund": {
                "cash": str(q_money(fund.cash)),
                "locked": str(q_money(fund.locked)),
                "total_value": str(q_money(fund.total_value)),
                "units": str(fund.units),
                "nav": str(q_nav(fund.nav)),
                "series_id": fund.series_id,
                "twr_pct": str(fund.twr),
                "bankrupt": fund.closed,
            },
            "simulation_energy": energy,
            "energy_max": self.settings.energy_max,
            "energy_per_wager": self.settings.energy_per_wager,
            "can_wager": energy_mod.can_wager(energy, cost=self.settings.energy_per_wager),
            "badges": list(badges),
            "cooldown": {
                "tier": cooldown.tier,
                "locked": cooldown.is_locked(self.clock.now()),
                "locked_until": (
                    cooldown.locked_until.isoformat() if cooldown.locked_until else None
                ),
                "max_hours": str(cap_hours),
                "solvent_streak": cooldown.solvent_streak,
                "solvent_days_per_tier": SOLVENT_DAYS_PER_TIER,
                "solvent_days_to_tier": max(0, SOLVENT_DAYS_PER_TIER - cooldown.solvent_streak),
                "last_solvent_day": (
                    cooldown.last_solvent_day.isoformat() if cooldown.last_solvent_day else None
                ),
            },
            "nav_history": [str(point) for point in series],
            "nav_at_matches": self._nav_at_matches(user_id, entries),
            "risk": {
                "sharpe_ratio": sharpe_ratio,
                "sortino_ratio": sortino_ratio,
                "max_drawdown_pct": max_drawdown,
                "beta": beta,
                "alpha": alpha,
                "risk_adjusted_score": risk_adjusted_score(twr, max_drawdown, sharpe_ratio),
                "reliability": reliability,
                "trade_stats": {
                    "total_trades": stats.total_trades,
                    "win_rate_pct": stats.win_rate_pct,
                    "profit_factor": stats.profit_factor,
                    "gross_profit": stats.gross_profit,
                    "gross_loss": stats.gross_loss,
                    "avg_win": stats.avg_win,
                    "avg_loss": stats.avg_loss,
                    "expectancy": stats.expectancy,
                },
            },
            "benchmarks": {
                "series": {
                    strategy.value: [str(point) for point in points]
                    for strategy, points in bench_series.items()
                },
                "latest": {
                    strategy.value: str(to_pct(points[-1] / dec("100") - ONE))
                    for strategy, points in bench_series.items()
                },
            },
            "pending_wagers": pending,
            "settled_wagers": settled,
        }

    @staticmethod
    def _wager_view(
        record: WagerRecord, stake: Money, payout: Money | None
    ) -> dict[str, object]:
        view: dict[str, object] = {
            "wager_id": record.wager_id,
            "match_id": record.match_id,
            "match_title": record.match_title,
            "market_type": record.market_type,
            "selection": record.selection,
            "odds": str(record.odds),
            "stake": str(q_money(stake)),
            "status": _settlement_status(stake, payout),
            "closing_odds": str(record.closing_odds) if record.closing_odds else None,
            "clv_pct": (
                str(clv_pct(record.odds, record.closing_odds)) if record.closing_odds else None
            ),
        }
        if payout is not None:
            view["payout"] = str(q_money(payout))
            view["net"] = str(q_money(payout - stake))
        return view
