"""Simülasyon enerjisi — politika katmanı (spec §4.1).

Saf fonksiyonlar: saat **enjekte edilir**, `datetime.now()` çağrılmaz. Böylece test edilebilir
ve deterministiktir.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

from .money import Money

MAX_ENERGY: int = 100
COST_PER_WAGER: int = 10
REGEN_PER_HOUR: Money = Decimal("10")
_SECONDS_PER_HOUR: Money = Decimal(3600)


def regen(
    energy: int,
    last_update: datetime,
    now: datetime,
    *,
    max_energy: int = MAX_ENERGY,
    per_hour: Money = REGEN_PER_HOUR,
) -> tuple[int, datetime]:
    """Geçen süreye göre enerjiyi yeniler; saati **kazanılan kadar** ilerletir.

    Kısmi ilerleme kaybolmaz: artan saat dilimi (`gained <= 0`) `last_update`'i ilerletmez,
    böylece 100 dakikalık beklemenin 4 dakikalık artığı saklanır.

    **Tavandayken geçen süre yanar** (batarya yok): `energy >= max_energy` ise `last_update`
    `now`'a çekilir. Yoksa oyuncu tavanda bekleyip biriktirdiği süreyi sonra arka arkaya
    bahislerle harcayabilir, yani tavan enerji depolamayı engelleyemezdi.
    """
    if energy >= max_energy:
        return max_energy, now
    if now <= last_update:
        return energy, last_update

    elapsed = Decimal((now - last_update).total_seconds())
    gained = int(elapsed * per_hour / _SECONDS_PER_HOUR)
    if gained <= 0:
        return energy, last_update

    new_energy = min(max_energy, energy + gained)
    advanced = timedelta(seconds=float(Decimal(gained) * _SECONDS_PER_HOUR / per_hour))
    return new_energy, last_update + advanced


def can_wager(energy: int, *, cost: int = COST_PER_WAGER) -> bool:
    """Enerji eşiğin altındaysa bahis reddedilir (HTTP 429)."""
    return energy >= cost


def spend(energy: int, *, cost: int = COST_PER_WAGER) -> int:
    """Bir bahsin enerji maliyetini düşer; taban 0."""
    return max(0, energy - cost)
