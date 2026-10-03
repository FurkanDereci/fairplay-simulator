"""Para ve sayı politikası.

Tek kural: **para `Decimal`, istatistik `float`.** Yuvarlama yalnız burada ve tek biçimde yapılır.
`float` kabul edilmez — ikili yuvarlama artıklarını gizlediği için (bkz. `AGENTS.md` §6).
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, getcontext

# Deterministlik: sabit ve AÇIK bir duyarlılık bağlamı (sistem varsayılanına bırakılmaz).
getcontext().prec = 28

Number = int | str | Decimal
Money = Decimal

BASE_NAV: Money = Decimal("100")
ZERO: Money = Decimal("0")
ONE: Money = Decimal("1")
TWO: Money = Decimal("2")

MONEY_Q: Money = Decimal("0.01")
NAV_Q: Money = Decimal("0.0001")
UNITS_Q: Money = Decimal("0.0000001")
PCT_Q: Money = Decimal("0.01")


def dec(value: Number) -> Money:
    """Decimal üretir. `float` kabul edilmez (bilinçli sınır)."""
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, str):
        return Decimal(value)
    raise TypeError(f"Decimal'e çevrilemez tip: {type(value).__name__}")


def q(value: Money, quantum: Money) -> Money:
    """Verilen kuantuma, ROUND_HALF_UP ile yuvarlar."""
    return value.quantize(quantum, rounding=ROUND_HALF_UP)


def q_money(value: Money) -> Money:
    return q(value, MONEY_Q)


def q_nav(value: Money) -> Money:
    return q(value, NAV_Q)


def q_units(value: Money) -> Money:
    return q(value, UNITS_Q)


def to_pct(fraction: Money) -> Money:
    """Oran → yüzde (0.15 → 15.00)."""
    return q(fraction * Decimal(100), PCT_Q)
