"""İflas sonrası kademeli kilit — politika katmanı (spec §4.2).

`T(n) = min(168, 4^(n−1))` saat; 3 ardışık solvent gün tier'ı bir düşürür.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from .money import Money

MAX_COOLDOWN_HOURS: Money = Decimal("168")
HOURS_BASE: Money = Decimal("4")
SOLVENT_DAYS_PER_TIER: int = 3


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


@dataclass
class CooldownState:
    """İflas kilidinin politika durumu. Saat daima dışarıdan verilir."""

    tier: int = 0
    solvent_streak: int = 0
    locked_until: datetime | None = None

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

        `max_hours` disiplin indirimini uygular (spec §4.2); varsayılan 168.
        """
        self.tier += 1
        self.solvent_streak = 0
        hours = cooldown_hours(self.tier, max_hours=max_hours)
        self.locked_until = now + timedelta(hours=float(hours))
        return hours

    def register_solvent_day(self) -> None:
        """Bir solvent günü kaydeder ve gerekirse tier'ı düşürür."""
        self.solvent_streak, self.tier = record_solvent_day(self.solvent_streak, self.tier)
