"""Append-only olay defteri — tek gerçek kaynak (bkz. ADR-0002).

`Ledger` yalnız kayıt tutar; durum **tutmaz**. Durum, `nav.Fund.replay` ile bu kayıtların
saf projeksiyonudur. Böylece "aynı mantık iki yerde" yapısal olarak imkânsızlaşır.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Any

from .errors import UnsupportedLedgerVersion
from .money import ZERO, Money

# Defter kayıt biçiminin sürümü. Alan/olay **eklemek** geriye uyumludur; var olanı
# **değiştirmek** bu numarayı artırır ve bir **upcaster** gerektirir (bkz. ADR-0009).
LEDGER_SCHEMA_VERSION = 1


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

    def as_dict(self) -> dict[str, Any]:
        """Kaydın **kararlı** metin biçimi (para `str` → tam hassasiyet korunur)."""
        return {
            "seq": self.seq,
            "entry_type": self.entry_type.value,
            "amount": str(self.amount),
            "stake": str(self.stake),
            "wager_id": self.wager_id,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> LedgerEntry:
        wager_id = payload.get("wager_id")
        return cls(
            seq=int(payload["seq"]),
            entry_type=EntryType(str(payload["entry_type"])),
            amount=Decimal(str(payload["amount"])),
            stake=Decimal(str(payload.get("stake", "0"))),
            wager_id=None if wager_id is None else str(wager_id),
        )


def decode_ledger(payload: Mapping[str, Any]) -> list[LedgerEntry]:
    """Donmuş defter kaydını çözer.

    Bilinmeyen şema sürümü **sessizce okunmaz**: eski sürüm bir *upcaster* ister, kodun
    tanımadığı yeni sürüm ise kod güncellemesi — ikisi de açık hata olarak döner.
    """
    version = payload.get("schema_version")
    if version != LEDGER_SCHEMA_VERSION:
        raise UnsupportedLedgerVersion(
            f"Defter şema sürümü {version!r}; bu kod {LEDGER_SCHEMA_VERSION} bekliyor. "
            "Eski sürüm için upcaster yazılmalı (ADR-0009)."
        )
    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise UnsupportedLedgerVersion("Defter kaydında 'entries' listesi yok.")
    return [LedgerEntry.from_dict(item) for item in entries]


def encode_ledger(entries: Sequence[LedgerEntry]) -> dict[str, Any]:
    """Kayıtları sürüm damgalı, yeniden üretilebilir bir belgeye çevirir."""
    return {
        "schema_version": LEDGER_SCHEMA_VERSION,
        "entries": [entry.as_dict() for entry in entries],
    }


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
