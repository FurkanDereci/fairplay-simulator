"""Oran matematiği — spec §3.

Vig/overround arındırma, fair odds, Kelly, EV ve CLV. Hepsi saf; oranlar `Decimal`.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal

from .money import ONE, ZERO, Money, q

PROB_Q: Money = Decimal("0.0000001")
ODDS_Q: Money = Decimal("0.01")
OVERRROUND_Q: Money = Decimal("0.0000001")
PCT_Q: Money = Decimal("0.01")


@dataclass(frozen=True)
class NormalizedMarket:
    market_type: str
    outcomes: dict[str, Money]
    implied: dict[str, Money]
    fair_prob: dict[str, Money]
    fair_odds: dict[str, Money]
    overround: Money
    margin_pct: Money


def normalize_market(market_type: str, outcomes: Mapping[str, Money]) -> NormalizedMarket:
    """Oranları arındırır: implied, overround/marj, fair olasılık ve fair odds.

    `O ≤ 0` olan sonuçlar atlanır (spec §5).
    """
    valid = {k: v for k, v in outcomes.items() if v > ZERO}
    implied = {k: ONE / v for k, v in valid.items()}
    total = sum(implied.values(), ZERO)
    overround = max(ZERO, total - ONE)
    margin = (overround / total * Decimal(100)) if total > ZERO else ZERO
    fair_prob = {k: v / total for k, v in implied.items()} if total > ZERO else {}
    fair_odds = {k: q(ONE / p, ODDS_Q) for k, p in fair_prob.items() if p > ZERO}

    return NormalizedMarket(
        market_type=market_type,
        outcomes=dict(valid),
        implied={k: q(v, PROB_Q) for k, v in implied.items()},
        fair_prob={k: q(v, PROB_Q) for k, v in fair_prob.items()},
        fair_odds=fair_odds,
        overround=q(overround, OVERRROUND_Q),
        margin_pct=q(margin, PCT_Q),
    )


def expected_value(probability: Money, odds: Money) -> Money:
    """Bahis başına birim getiri beklentisi: `p·o − 1`."""
    return probability * odds - ONE


def kelly_fraction(probability: Money, odds: Money) -> Money:
    """Kelly stake oranı, tam hassasiyetle: `max(0, (p·o − 1)/(o − 1))`.

    `O ≤ 1` ise 0. Raporlarken 4 ondalığa yuvarlanır (ör. 0.1409 → %14.09).
    """
    if odds <= ONE:
        return ZERO
    fraction = (probability * odds - ONE) / (odds - ONE)
    return fraction if fraction > ZERO else ZERO


def clv_pct(placed_odds: Money, closing_odds: Money) -> Money:
    """Closing Line Value (%): `(o_konulan/o_kapanış − 1) × 100`."""
    if closing_odds <= ZERO:
        return ZERO
    return q((placed_odds / closing_odds - ONE) * Decimal(100), PCT_Q)
