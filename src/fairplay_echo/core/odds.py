"""Oran matematiği — spec §3.

Vig/overround arındırma, fair odds, Kelly, EV ve CLV. Hepsi saf; oranlar `Decimal`.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal

from .errors import InvalidOdds
from .money import ONE, ZERO, Money, q

PROB_Q: Money = Decimal("0.0000001")
ODDS_Q: Money = Decimal("0.01")
OVERRROUND_Q: Money = Decimal("0.0000001")
PCT_Q: Money = Decimal("0.01")

#: Pazar başına **zorunlu** sonuçlar. Eksik besleme sınırda reddedilir (Suite 3).
_REQUIRED_OUTCOMES: dict[str, frozenset[str]] = {
    "1X2": frozenset({"HOME", "DRAW", "AWAY"}),
    "OVER_UNDER_2.5": frozenset({"OVER_2.5", "UNDER_2.5"}),
    "BTTS": frozenset({"BTTS_YES", "BTTS_NO"}),
}


@dataclass(frozen=True)
class NormalizedMarket:
    market_type: str
    outcomes: dict[str, Money]
    implied: dict[str, Money]
    fair_prob: dict[str, Money]
    fair_odds: dict[str, Money]
    overround: Money
    margin_pct: Money


def validate_market_odds(market_type: str, outcomes: Mapping[str, Money]) -> None:
    """Oran dizisini **sınırda** denetler; bozuksa `InvalidOdds` yükseltir (Suite 3).

    Üç kural: pazarın zorunlu sonuçları eksiksiz olmalı · her oran `> 1` olmalı (`O ≤ 1`
    matematiksel olarak imkânsız orandır) · toplam ima edilen olasılık `Σ(1/o) > 1` olmalı
    (aksi hâlde **negatif vig** vardır: bahisçi lehine garanti kâr, gerçek oran dizisinde olamaz).

    Bozuk besleme **reddedilir, kırpılmaz**: `overround = max(0, …)` ile gizlemek, onu kabul
    etmekten kötüdür (`docs/70` §7.2). Bu yüzden denetim `normalize_market`'ın *dışında*, girdinin
    sisteme girdiği yerde durur.
    """
    if not outcomes:
        raise InvalidOdds("Oran dizisi boş.")
    required = _REQUIRED_OUTCOMES.get(market_type)
    if required is not None:
        missing = required - set(outcomes)
        if missing:
            raise InvalidOdds(f"{market_type} pazarında eksik sonuç: {sorted(missing)}.")
    for selection, price in outcomes.items():
        if price <= ONE:
            raise InvalidOdds(f"{selection}: oran 1'den büyük olmalı (verilen {price}).")
    total = sum((ONE / price for price in outcomes.values()), ZERO)
    if total <= ONE:
        raise InvalidOdds(
            f"Toplam ima edilen olasılık {q(total, OVERRROUND_Q)} ≤ 1 — negatif vig reddedilir."
        )


def normalize_market(market_type: str, outcomes: Mapping[str, Money]) -> NormalizedMarket:
    """Oranları arındırır: implied, overround/marj, fair olasılık ve fair odds.

    `O ≤ 0` olan sonuçlar atlanır (spec §5). Bu fonksiyon **saf**tır: bozuk beslemeyi denetlemek
    `validate_market_odds`'un işidir (sınırda reddedilir, burada kırpılmaz).
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


def risk_of_ruin(edge: Money, units: Money) -> Money:
    """İflas riski yüzdesi — spec §3.4.

    `R_ruin = ((1−Edge)/(1+Edge))^Units × 100`. Burada `Edge` bahis başına beklenen getiri
    (`p·o − 1`) ve `Units` kasadaki eşit-bahis sayısıdır (`cash/stake`).

    Kenar pozitif değilse oran ≥ 1 olur, yani iflas **kaçınılmazdır**: formül negatif sayı
    üretmesin diye `100.00` döner. `Units ≤ 0` (bahis kasayı aşıyor) hâlinde de 100 döner.
    """
    if edge <= ZERO or units <= ZERO:
        return q(Decimal(100), PCT_Q)
    ratio = (ONE - edge) / (ONE + edge)
    return q(ratio**units * Decimal(100), PCT_Q)
