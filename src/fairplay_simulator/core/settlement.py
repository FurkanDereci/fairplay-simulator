"""Kupon sonuçlandırma — spec §5 kenar durumları.

Ödeme kuralları burada **tek** yerde yaşar. Karar (hangi sonuç) sunucudan gelir; istemci bildirmez.
"""

from __future__ import annotations

from enum import Enum

from .ledger import Ledger, LedgerEntry
from .money import ONE, TWO, ZERO, Money, q_money


class Outcome(str, Enum):
    WON = "WON"
    LOST = "LOST"
    VOID = "VOID"
    PUSH = "PUSH"
    HALF_WON = "HALF_WON"
    HALF_LOST = "HALF_LOST"


def payout_for(outcome: Outcome, stake: Money, odds: Money) -> Money:
    """Sonuca göre ödeme. VOID/PUSH iadedir (net 0)."""
    if outcome is Outcome.WON:
        return q_money(stake * odds)
    if outcome is Outcome.LOST:
        return ZERO
    if outcome in (Outcome.VOID, Outcome.PUSH):
        return stake
    if outcome is Outcome.HALF_WON:
        return q_money(stake + stake * (odds - ONE) / TWO)
    if outcome is Outcome.HALF_LOST:
        return q_money(stake / TWO)
    raise ValueError(f"Bilinmeyen sonuç: {outcome!r}")


def settle(
    ledger: Ledger, wager_id: str, stake: Money, odds: Money, outcome: Outcome
) -> LedgerEntry:
    """Kuponu sonuçlandırır ve deftere işler."""
    return ledger.settle_wager(wager_id, stake, payout_for(outcome, stake, odds))
