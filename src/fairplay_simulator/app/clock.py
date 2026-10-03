"""Saat soyutlaması.

Çekirdek `datetime.now()` çağırmaz; saat enjekte edilir. Testler `FixedClock` ile zamanı kaydırır,
enerji yenilenmesi ve cooldown bitişi uyumadan test edilebilir.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Protocol, runtime_checkable


@runtime_checkable
class Clock(Protocol):
    def now(self) -> datetime: ...


class SystemClock:
    """Gerçek saat (UTC)."""

    def now(self) -> datetime:
        return datetime.now(timezone.utc)


class FixedClock:
    """Test için sabit saat."""

    def __init__(self, moment: datetime) -> None:
        self._moment = moment

    def now(self) -> datetime:
        return self._moment

    def advance(self, *, seconds: float = 0.0, hours: float = 0.0) -> None:
        self._moment = self._moment + timedelta(seconds=seconds, hours=hours)
