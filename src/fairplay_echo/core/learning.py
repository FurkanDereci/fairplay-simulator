"""Öğrenme ölçütleri — "bu simülatör öğretir" iddiasını **ölçülebilir** kılmak (docs/90).

Neden var: "öğretir" yanlışlanamaz bir cümledir. Yerine kullanıcının **kendi davranışı** sayıya
dökülür: kapanış çizgisini geçebiliyor mu (CLV eğilimi), bahis boyutu portföye göre ölçülü mü,
favori yanlılığı var mı, pazar çeşitliliği nasıl. Hepsi defterden türer; ürün **tavsiye vermez**,
yalnızca gösterir — kararı kullanıcı verir (ADR-0006).

Eşikler **politika** değerleridir, doğa yasası değil: gerekçeleri `docs/90`'da yazılıdır.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal

from .ledger import EntryType, LedgerEntry
from .money import ZERO, Money, q
from .nav import Fund
from .odds import clv_pct

#: Bu sayının altında hiçbir eğilim okunmaz (alan 3'ün örneklem kuralıyla aynı mantık).
MIN_SAMPLE = 6
#: Ortalama bahis / portföy üst sınırı. Tam Kelly tavanı; üstü "aşırı".
STAKE_RATIO_LIMIT: Money = Decimal("0.15")
#: "Favori" tanımı: bu oranın altına oynanan bahisler.
FAVOURITE_LINE: Money = Decimal("2.00")
#: Favori payı bu sınırı geçerse yanlılık uyarısı.
FAVOURITE_SHARE_LIMIT: Money = Decimal("0.70")
#: CLV yarılar arası farkın "eğilim" sayılması için gereken bant (yüzde puanı).
CLV_TREND_BAND: Money = Decimal("1.00")

_RATIO_Q: Money = Decimal("0.0001")
PCT_Q: Money = Decimal("0.01")

TREND_UP = "iyileşiyor"
TREND_FLAT = "yatay"
TREND_DOWN = "kötüleşiyor"
TREND_UNKNOWN = "örneklem yetersiz"


@dataclass(frozen=True)
class BetInput:
    """Deptodan gelen, çekirdeğin ihtiyaç duyduğu bahis alanları (DB tipi sızmaz)."""

    wager_id: str
    market_type: str
    odds: Money
    closing_odds: Money | None


@dataclass(frozen=True)
class BetObservation:
    market_type: str
    odds: Money
    clv_pct: Money | None
    stake_ratio: Money


@dataclass(frozen=True)
class LearningReport:
    bets: int
    reliable: bool
    market_breadth: int
    clv_mean_pct: Money | None
    clv_first_half_pct: Money | None
    clv_second_half_pct: Money | None
    clv_trend: str
    mean_stake_ratio_pct: Money | None
    stake_verdict: str
    favourite_share_pct: Money | None
    favourite_verdict: str
    headline: str


def observations(
    entries: Sequence[LedgerEntry], bets: Mapping[str, BetInput]
) -> list[BetObservation]:
    """Bahisleri defter sırasıyla gezip **bahis anındaki** portföy değerini yakalar.

    NAV değil **portföy değeri** kullanılır: NAV birim fiyatıdır (100 tabanlı), bahis boyutu ise
    portföyün yüzdesi olarak anlamlıdır.
    """
    fund = Fund()
    found: list[BetObservation] = []
    for entry in entries:
        if entry.entry_type is EntryType.WAGER_PLACED and entry.wager_id is not None:
            bet = bets.get(entry.wager_id)
            value = fund.total_value
            if bet is not None and value > ZERO:
                closing = bet.closing_odds
                found.append(
                    BetObservation(
                        market_type=bet.market_type,
                        odds=bet.odds,
                        clv_pct=None if closing is None else clv_pct(bet.odds, closing),
                        stake_ratio=q(entry.amount / value, _RATIO_Q),
                    )
                )
        fund.apply(entry)
    return found


def _mean(values: Sequence[Money]) -> Money | None:
    if not values:
        return None
    return sum(values, ZERO) / Decimal(len(values))


def clv_trend(values: Sequence[Money]) -> tuple[Money | None, Money | None, str]:
    """CLV'nin ilk yarısı ile ikinci yarısını karşılaştırır.

    Yön, **kapanış çizgisini geçme** becerisinin zamanla değişip değişmediğini gösterir; tek bir
    bahsin CLV'i gürültüdür, yarıların ortalaması sinyaldir.
    """
    if len(values) < MIN_SAMPLE:
        return (None, None, TREND_UNKNOWN)
    half = len(values) // 2
    first = _mean(values[:half])
    second = _mean(values[half:])
    if first is None or second is None:  # pragma: no cover - MIN_SAMPLE bunu imkânsız kılar
        return (None, None, TREND_UNKNOWN)
    delta = second - first
    if delta >= CLV_TREND_BAND:
        return (first, second, TREND_UP)
    if delta <= -CLV_TREND_BAND:
        return (first, second, TREND_DOWN)
    return (first, second, TREND_FLAT)


def _pct_text(value: Money) -> str:
    """Metin içindeki yüzde **tr-TR** yazılır (virgül): kullanıcı dili.

    Oranlar nokta kalır (bahisçi konvansiyonu, `AGENTS.md` §9); yüzdeler virgülle yazılır.
    """
    return f"{value}".replace(".", ",")


def build_learning_report(
    entries: Sequence[LedgerEntry], bets: Mapping[str, BetInput]
) -> LearningReport:
    seen = observations(entries, bets)
    count = len(seen)
    reliable = count >= MIN_SAMPLE

    clvs = [item.clv_pct for item in seen if item.clv_pct is not None]
    first, second, trend = clv_trend(clvs)
    clv_mean = _mean(clvs)

    ratio = _mean([item.stake_ratio for item in seen])
    ratio_pct = None if ratio is None else q(ratio * Decimal(100), PCT_Q)
    stake_verdict = "—" if ratio is None else ("aşırı" if ratio > STAKE_RATIO_LIMIT else "ölçülü")

    favourites = sum(1 for item in seen if item.odds < FAVOURITE_LINE)
    favourite_share = None if count == 0 else Decimal(favourites) / Decimal(count)
    favourite_pct = None if favourite_share is None else q(favourite_share * Decimal(100), PCT_Q)
    favourite_limit_pct = q(FAVOURITE_SHARE_LIMIT * Decimal(100), PCT_Q)
    favourite_verdict = (
        "—"
        if favourite_pct is None
        else ("favori ağırlıklı" if favourite_pct > favourite_limit_pct else "dengeli")
    )

    limit_pct = q(STAKE_RATIO_LIMIT * Decimal(100), PCT_Q)
    parts: list[str] = []
    if reliable:
        if stake_verdict == "aşırı" and ratio_pct is not None:
            parts.append(
                f"ortalama bahis portföyün %{_pct_text(ratio_pct)} seviyesinde "
                f"(sınır %{_pct_text(limit_pct)})"
            )
        if favourite_verdict == "favori ağırlıklı" and favourite_pct is not None:
            # Ek uyumu ("%100,00'ü" / "%10,00'u") yüzünden ek gerektirmeyen kalıp kullanılır.
            parts.append(f"favori oranı %{_pct_text(favourite_pct)} — yanlılık riski")
        if trend == TREND_UP:
            parts.append("CLV eğilimi yukarı")
        elif trend == TREND_DOWN:
            parts.append("CLV eğilimi aşağı")

    headline = (
        f"Örneklem yetersiz ({count}/{MIN_SAMPLE}) — eğilim okunmaz."
        if not reliable
        else ("; ".join(parts) if parts else "belirgin bir eğilim yok")
    )

    return LearningReport(
        bets=count,
        reliable=reliable,
        market_breadth=len({item.market_type for item in seen}),
        clv_mean_pct=None if clv_mean is None else q(clv_mean, PCT_Q),
        clv_first_half_pct=None if first is None else q(first, PCT_Q),
        clv_second_half_pct=None if second is None else q(second, PCT_Q),
        clv_trend=trend,
        mean_stake_ratio_pct=ratio_pct,
        stake_verdict=stake_verdict,
        favourite_share_pct=favourite_pct,
        favourite_verdict=favourite_verdict,
        headline=headline,
    )
