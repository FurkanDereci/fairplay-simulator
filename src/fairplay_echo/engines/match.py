"""Maç motoru: tohumlu Poisson + Monte Carlo.

Determinizm: tüm rastgelelik enjekte edilen `random.Random(seed)` üzerinden gelir; aynı seed
**her zaman** aynı sonucu verir. Lambda türetme heuristiği ADR-0003'te kayıtlıdır.
"""

from __future__ import annotations

import math
import random
from collections.abc import Mapping
from dataclasses import dataclass

from ..core.money import Money
from ..core.odds import normalize_market

MARKET_1X2 = "1X2"
MARKET_OU_25 = "OVER_UNDER_2.5"
MARKET_BTTS = "BTTS"

OVER = "OVER_2.5"
UNDER = "UNDER_2.5"
BTTS_YES = "BTTS_YES"
BTTS_NO = "BTTS_NO"

LEAGUE_AVERAGE_GOALS = 2.6


@dataclass(frozen=True)
class MatchEvent:
    """Maç içi olay — dakika, takım, tür ve anlık skoru taşıyan açıklama."""

    minute: int
    team: str
    event_type: str
    description: str


@dataclass(frozen=True)
class MatchResult:
    match_id: str
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    events: tuple[MatchEvent, ...] = ()

    @property
    def outcome_1x2(self) -> str:
        if self.home_score > self.away_score:
            return "HOME"
        if self.home_score < self.away_score:
            return "AWAY"
        return "DRAW"

    @property
    def outcome_ou_25(self) -> str:
        return OVER if self.home_score + self.away_score >= 3 else UNDER

    @property
    def outcome_btts(self) -> str:
        return BTTS_YES if self.home_score > 0 and self.away_score > 0 else BTTS_NO

    def outcome_for(self, market_type: str) -> str:
        """Pazar tipine göre kazanan seçimi döner; bilinmeyen market `ValueError`."""
        if market_type == MARKET_1X2:
            return self.outcome_1x2
        if market_type == MARKET_OU_25:
            return self.outcome_ou_25
        if market_type == MARKET_BTTS:
            return self.outcome_btts
        raise ValueError(f"Bilinmeyen market tipi: {market_type!r}")


@dataclass(frozen=True)
class MonteCarloSummary:
    iterations: int
    home_win_pct: float
    draw_pct: float
    away_win_pct: float
    over_25_pct: float
    btts_pct: float


@dataclass(frozen=True)
class MatchRecord:
    """Kalıcı maç kaydı; sonuç ve kullanılan oran/tohum birlikte saklanır.

    Benchmark botları bu kayıtlardan **yeniden türetilir** — ayrı bot durumu tutulmaz.
    """

    match_id: str
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    odds_1x2: Mapping[str, Money]
    seed: int | None

    @property
    def result(self) -> MatchResult:
        return MatchResult(
            match_id=self.match_id,
            home_team=self.home_team,
            away_team=self.away_team,
            home_score=self.home_score,
            away_score=self.away_score,
        )


def derive_lambdas(
    odds_1x2: Mapping[str, Money], *, expected_total: float = LEAGUE_AVERAGE_GOALS
) -> tuple[float, float]:
    """Fair olasılıklardan takım başına beklenen gol (λ) üretir.

    Favori, toplam golün daha büyük payını alır (bkz. ADR-0003).
    """
    market = normalize_market(MARKET_1X2, odds_1x2)
    home = float(market.fair_prob.get("HOME", Money("0")))
    away = float(market.fair_prob.get("AWAY", Money("0")))
    decisive = home + away
    home_share = home / decisive if decisive > 0 else 0.5
    return expected_total * home_share, expected_total * (1.0 - home_share)


def _poisson(rng: random.Random, lam: float) -> int:
    """Knuth örneklemesi — tohumlu rng ile deterministik."""
    if lam <= 0.0:
        return 0
    limit = math.exp(-lam)
    goals = 0
    product = 1.0
    while True:
        product *= rng.random()
        if product <= limit:
            return goals
        goals += 1


def _goal_minutes(rng: random.Random, home_goals: int, away_goals: int) -> list[tuple[int, str]]:
    """Gol dakikalarını üretir ve sıralar. **Gol sayısı çekildikten SONRA** çağrılır ki
    olay üretimi mevcut tohumların skorlarını değiştirmesin."""
    slots = ("HOME",) * home_goals + ("AWAY",) * away_goals
    timed = [(rng.randint(1, 90), side) for side in slots]
    timed.sort(key=lambda item: item[0])
    return timed


def _build_events(
    rng: random.Random, home_goals: int, away_goals: int, home_team: str, away_team: str
) -> tuple[MatchEvent, ...]:
    """Gol olaylarını zaman çizelgesine çevirir; açıklama anlık skoru içerir."""
    home = away = 0
    events: list[MatchEvent] = []
    for minute, side in _goal_minutes(rng, home_goals, away_goals):
        if side == "HOME":
            home += 1
            team = home_team
        else:
            away += 1
            team = away_team
        events.append(
            MatchEvent(
                minute=minute,
                team=team,
                event_type="GOAL",
                description=f"{minute}. dakika — {team} golü ({home}-{away})",
            )
        )
    return tuple(events)


def simulate_match(
    match_id: str,
    home_team: str,
    away_team: str,
    odds_1x2: Mapping[str, Money],
    *,
    seed: int | None = None,
) -> MatchResult:
    """Tek maç simüle eder. Aynı `seed` → aynı skor **ve aynı olay zaman çizelgesi**."""
    lambda_home, lambda_away = derive_lambdas(odds_1x2)
    rng = random.Random(seed)
    home_score = _poisson(rng, lambda_home)
    away_score = _poisson(rng, lambda_away)
    events = _build_events(rng, home_score, away_score, home_team, away_team)
    return MatchResult(
        match_id=match_id,
        home_team=home_team,
        away_team=away_team,
        home_score=home_score,
        away_score=away_score,
        events=events,
    )


def run_monte_carlo(
    lambda_home: float,
    lambda_away: float,
    iterations: int,
    *,
    seed: int | None = None,
) -> MonteCarloSummary:
    """Verilen λ'lar için N koşu; frekansları yüzde olarak döner."""
    if iterations < 1:
        raise ValueError("iterations >= 1 olmalı.")

    rng = random.Random(seed)
    home_wins = draws = away_wins = overs = btts = 0
    for _ in range(iterations):
        home_score = _poisson(rng, lambda_home)
        away_score = _poisson(rng, lambda_away)
        if home_score > away_score:
            home_wins += 1
        elif home_score == away_score:
            draws += 1
        else:
            away_wins += 1
        if home_score + away_score >= 3:
            overs += 1
        if home_score > 0 and away_score > 0:
            btts += 1

    def pct(count: int) -> float:
        return round(count / iterations * 100.0, 2)

    return MonteCarloSummary(
        iterations=iterations,
        home_win_pct=pct(home_wins),
        draw_pct=pct(draws),
        away_win_pct=pct(away_wins),
        over_25_pct=pct(overs),
        btts_pct=pct(btts),
    )
