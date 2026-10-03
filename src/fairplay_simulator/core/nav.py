"""Birimleştirme (GIPS Unit NAV) — saf projeksiyon.

`Fund` tek mutasyon yüzeyine sahiptir: `apply`. Bakiye/NAV bu yüzeyin sonucudur, kaynağı değil.
Formüller `docs/20-accounting-spec.md` §1 ile birebir aynıdır.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from .errors import (
    AlreadySettled,
    DuplicateWager,
    InsufficientCash,
    InvalidAmount,
    UnknownWager,
)
from .ledger import EntryType, LedgerEntry
from .metrics import SettledWager
from .money import BASE_NAV, ONE, ZERO, Money, to_pct


@dataclass
class Fund:
    """Birimleştirilmiş fonun durumu (projeksiyon)."""

    base_nav: Money = BASE_NAV
    cash: Money = ZERO
    locked: Money = ZERO
    units: Money = ZERO
    nav: Money = ZERO
    series_id: int = 1
    series_growth: Money = ONE
    closed: bool = False
    open_wagers: dict[str, Money] = field(default_factory=dict)
    settled_wagers: set[str] = field(default_factory=set)

    @property
    def total_value(self) -> Money:
        return self.cash + self.locked

    @property
    def twr(self) -> Money:
        """Zaman-ağırlıklı getiri (%), seriler arası **bileşik** — spec §1.5, I4."""
        growth = self.series_growth * (self.nav / self.base_nav)
        return to_pct(growth - ONE)

    def _recompute_nav(self) -> None:
        self.nav = self.total_value / self.units if self.units > ZERO else ZERO

    def apply(self, entry: LedgerEntry) -> None:
        kind = entry.entry_type
        if kind is EntryType.DEPOSIT:
            self._apply_deposit(entry)
        elif kind is EntryType.REFILL:
            self._apply_refill(entry)
        elif kind is EntryType.WAGER_PLACED:
            self._apply_placed(entry)
        elif kind is EntryType.WAGER_SETTLED:
            self._apply_settled(entry)
        else:  # pragma: no cover - enum kapalı olduğu için ulaşılamaz
            raise ValueError(f"Bilinmeyen kayıt tipi: {kind!r}")

    def _apply_deposit(self, entry: LedgerEntry) -> None:
        if entry.amount <= ZERO:
            raise InvalidAmount("Yatırım tutarı pozitif olmalı.")
        self.cash = entry.amount
        self.locked = ZERO
        self.units = entry.amount / self.base_nav
        self.nav = self.base_nav
        self.closed = False

    def _apply_refill(self, entry: LedgerEntry) -> None:
        if entry.amount <= ZERO:
            raise InvalidAmount("Refill tutarı pozitif olmalı.")
        if self.closed or self.units <= ZERO:
            # İflas sonrası yeniden birimleştirme: yeni seri, NAV = base.
            self.series_id += 1
            self.cash = entry.amount
            self.locked = ZERO
            self.units = entry.amount / self.base_nav
            self.nav = self.base_nav
            self.closed = False
        else:
            # Güncel NAV'dan yeni birim ihraç edilir; NAV **taşınır**, yeniden hesaplanmaz (I1).
            # Sonsuz hassasiyette V/U zaten değişmez; yeniden hesaplamak yuvarlama artığı sokar.
            self.units += entry.amount / self.nav
            self.cash += entry.amount

    def _apply_placed(self, entry: LedgerEntry) -> None:
        wager_id = entry.wager_id
        if wager_id is None:
            raise InvalidAmount("WAGER_PLACED için wager_id zorunlu.")
        if wager_id in self.open_wagers or wager_id in self.settled_wagers:
            raise DuplicateWager(wager_id)
        if entry.amount <= ZERO:
            raise InvalidAmount("Bahis tutarı pozitif olmalı.")
        if entry.amount > self.cash:
            raise InsufficientCash(wager_id)
        self.cash -= entry.amount
        self.locked += entry.amount
        self.open_wagers[wager_id] = entry.amount
        # NAV değişmez: yalnız kasa → kilitli transferi (spec §1.1). Yeniden hesap artık sokar.

    def _apply_settled(self, entry: LedgerEntry) -> None:
        wager_id = entry.wager_id
        if wager_id is None:
            raise UnknownWager("<yok>")
        if wager_id in self.settled_wagers:
            raise AlreadySettled(wager_id)
        if wager_id not in self.open_wagers:
            raise UnknownWager(wager_id)
        stake = self.open_wagers[wager_id]
        if entry.stake != stake:
            raise InvalidAmount(f"Stake tutarsız: kayıt {entry.stake}, açık kupon {stake}.")
        if entry.amount < ZERO:
            raise InvalidAmount("Ödeme negatif olamaz.")

        del self.open_wagers[wager_id]
        self.settled_wagers.add(wager_id)
        self.locked -= stake
        self.cash += entry.amount
        self._recompute_nav()

        if self.total_value <= ZERO:
            # Seri kapanır; büyüme çarpanına yazılır → iflas kalıcı leke (I4).
            self.series_growth *= self.nav / self.base_nav
            self.closed = True

    @classmethod
    def replay(cls, entries: Iterable[LedgerEntry]) -> Fund:
        """Kayıtları baştan uygulayarak durumu üretir (I2)."""
        fund = cls()
        for entry in entries:
            fund.apply(entry)
        return fund


def nav_series(entries: Iterable[LedgerEntry]) -> list[Money]:
    """Her kayıttan sonraki NAV — metriklerin ve grafiğin girdisi."""
    fund = Fund()
    series: list[Money] = []
    for entry in entries:
        fund.apply(entry)
        series.append(fund.nav)
    return series


def settled_outcomes(entries: Iterable[LedgerEntry]) -> list[SettledWager]:
    """Defterdeki sonuçlanma kayıtlarını işlem istatistiği girdisine çevirir."""
    return [
        SettledWager(stake=entry.stake, payout=entry.amount)
        for entry in entries
        if entry.entry_type is EntryType.WAGER_SETTLED
    ]
