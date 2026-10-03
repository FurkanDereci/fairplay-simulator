"""İflas sonrası kademeli kilit — politika katmanı (spec §4.2).

`T(n) = min(max_hours, 4^(n−1))` saat; 3 ardışık **solvent gün** tier'ı bir düşürür. Gün sınırı
duvar saatiyle ölçülür: ilerleme yalnız **etkileşim anında** gözlenir (spec §4.2, sınır notu).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal

from .money import Money

MAX_COOLDOWN_HOURS: Money = Decimal("168")
HOURS_BASE: Money = Decimal("4")
SOLVENT_DAYS_PER_TIER: int = 3
#: Tek seferde işlenebilecek en fazla gün sınırı: uzun aradan sonra döngü şişmesin.
MAX_ACCRUAL_DAYS: int = 30


def cooldown_hours(tier: int, *, max_hours: Money = MAX_COOLDOWN_HOURS) -> Money:
    """Tier n için kilit süresi (saat). Tier < 1 → 0.

    `max_hours` **tavan**: disiplin indirimi bunu 168'den 72'ye çeker (spec §4.2). Varsayılan
    değişmez, böylece indirimsiz davranış aynen korunur.
    """
    if tier < 1:
        return Decimal(0)
    return min(max_hours, HOURS_BASE ** (tier - 1))


def record_solvent_day(streak: int, tier: int) -> tuple[int, int]:
    """Bir solvent günü işler; 3'e ulaşınca tier'ı bir düşürür ve seriyi sıfırlar."""
    streak += 1
    if streak >= SOLVENT_DAYS_PER_TIER:
        return 0, max(0, tier - 1)
    return streak, tier


def elapsed_days(last: date | None, today: date) -> int:
    """`last`tan `today`e geçen gün sınırı sayısı, `0..MAX_ACCRUAL_DAYS` aralığında.

    `last is None` (sayaç kurulmamış) → 0: ilk gözlem yalnız imleci kurar, geçmiş gün uydurmaz.
    Geriye giden tarih de 0 döner.
    """
    if last is None or today <= last:
        return 0
    return min((today - last).days, MAX_ACCRUAL_DAYS)


@dataclass
class CooldownState:
    """İflas kilidinin politika durumu. Saat daima dışarıdan verilir."""

    tier: int = 0
    solvent_streak: int = 0
    locked_until: datetime | None = None
    #: Solvent gün sayacının imleci (UTC günü). `None` = henüz kurulmadı.
    last_solvent_day: date | None = None

    def is_locked(self, now: datetime) -> bool:
        return self.locked_until is not None and now < self.locked_until

    def unlock_if_expired(self, now: datetime) -> bool:
        """Süresi dolmuşsa kilidi açar; açtıysa True döner."""
        if self.locked_until is not None and now >= self.locked_until:
            self.locked_until = None
            return True
        return False

    def trigger(self, now: datetime, *, max_hours: Money = MAX_COOLDOWN_HOURS) -> Money:
        """İflası işler: tier artar, kilit `T(tier)` saat sonrasına kurulur.

        `max_hours` disiplin indirimini uygular (spec §4.2); varsayılan 168. İmleç **bugüne**
        çekilir: iflastan önceki günler yeni sayaca taşınmaz (seri sıfırlanır).
        """
        self.tier += 1
        self.solvent_streak = 0
        self.last_solvent_day = now.date()
        hours = cooldown_hours(self.tier, max_hours=max_hours)
        self.locked_until = now + timedelta(hours=float(hours))
        return hours

    def register_solvent_day(self) -> None:
        """Bir solvent günü kaydeder ve gerekirse tier'ı düşürür."""
        self.solvent_streak, self.tier = record_solvent_day(self.solvent_streak, self.tier)

    def accrue_solvent_days(self, today: date, *, solvent: bool) -> int:
        """Gün sınırını işler; **sayılan** solvent gün sayısını döner.

        `solvent` false ise (hesap iflasta) hiç gün sayılmaz ama imleç yine ilerler: iflasta geçen
        günler **kaybedilir**, sonradan toplanamaz. İmleç `None` ise yalnız kurulur.
        """
        days = elapsed_days(self.last_solvent_day, today)
        if days == 0:
            if self.last_solvent_day is None:
                self.last_solvent_day = today
            return 0
        if solvent:
            for _ in range(days):
                self.register_solvent_day()
        self.last_solvent_day = today
        return days if solvent else 0
