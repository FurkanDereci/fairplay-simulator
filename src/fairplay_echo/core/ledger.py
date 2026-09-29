"""Append-only olay defteri — tek gerçek kaynak (bkz. ADR-0002).

`Ledger` yalnız kayıt tutar; durum **tutmaz**. Durum, `nav.Fund.replay` ile bu kayıtların
saf projeksiyonudur. Böylece "aynı mantık iki yerde" yapısal olarak imkânsızlaşır.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .money import ZERO, Money


class EntryType(str, Enum):
    """Deftere düşen olay tipleri.

    Not: seri kapanışı ayrı bir olay değildir; V=0'a indiği sonuçlanma kaydından **türetilir**
    (deterministik projeksiyon kuralı, `docs/10-domain-model.md` §2.2).
    """

    DEPOSIT = "DEPOSIT"
    REFILL = "REFILL"
    WAGER_PLACED = "WAGER_PLACED"
    WAGER_SETTLED = "WAGER_SETTLED"


@dataclass(frozen=True)
class LedgerEntry:
    """Tek bir olay. `seq` sıra numarasıdır; kayıtlar değişmez (frozen)."""

    seq: int
    entry_type: EntryType
    amount: Money = ZERO
    stake: Money = ZERO
    wager_id: str | None = None


class Ledger:
    """Sıralı, append-only kayıt dizisi."""

    def __init__(self) -> None:
        self._entries: list[LedgerEntry] = []

    @property
    def entries(self) -> tuple[LedgerEntry, ...]:
        return tuple(self._entries)

    def __len__(self) -> int:
        return len(self._entries)

    def deposit(self, amount: Money) -> LedgerEntry:
        """Fonu açar / başlangıç yatırımı (NAV = base)."""
        return self._append(EntryType.DEPOSIT, amount=amount)

    def refill(self, amount: Money) -> LedgerEntry:
        """Sanal bakiye ekleme — NAV'ı değiştirmez (I1)."""
        return self._append(EntryType.REFILL, amount=amount)

    def place_wager(self, wager_id: str, stake: Money) -> LedgerEntry:
        return self._append(EntryType.WAGER_PLACED, amount=stake, wager_id=wager_id)

    def settle_wager(self, wager_id: str, stake: Money, payout: Money) -> LedgerEntry:
        return self._append(
            EntryType.WAGER_SETTLED, amount=payout, stake=stake, wager_id=wager_id
        )

    def _append(
        self,
        entry_type: EntryType,
        *,
        amount: Money = ZERO,
        stake: Money = ZERO,
        wager_id: str | None = None,
    ) -> LedgerEntry:
        entry = LedgerEntry(
            seq=len(self._entries) + 1,
            entry_type=entry_type,
            amount=amount,
            stake=stake,
            wager_id=wager_id,
        )
        self._entries.append(entry)
        return entry
