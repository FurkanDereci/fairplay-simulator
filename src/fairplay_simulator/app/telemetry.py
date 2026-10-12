"""İstek telemetrisi — rate limiting ertelemesinin **gözlenebilir** koşulu (ADR-0021).

Süreç-içi, kalıcı olmayan sayaçlar: kimlik (istemci host'u) başına istek, 429 (hız sınırı) sayısı ve
tekil kimlik sayısı. Amaç: `docs/30` "gerçek kötüye kullanım gözlemlenene kadar" koşulunu
**görünmez** olmaktan çıkarıp ölçülebilir kılmak (PM Ö-11). Sunucu yeniden başlarsa sayaçlar
sıfırlanır — bu bilinçlidir (kalıcılık gerekmez; amaç anlık davranış, tarih değil).
"""

from __future__ import annotations

import threading
import time
from collections import Counter
from dataclasses import dataclass, field


@dataclass
class Telemetry:
    started_at: float = field(default_factory=time.monotonic)
    _requests: Counter[str] = field(default_factory=Counter, repr=False)
    _rate_limited: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def record_request(self, identity: str) -> None:
        """Bir API isteğini kimliğine göre sayar."""
        with self._lock:
            self._requests[identity] += 1

    def record_rate_limited(self) -> None:
        """429 (enerji/hız sınırı) yanıtını sayar — istismarın ilk işareti."""
        with self._lock:
            self._rate_limited += 1

    def snapshot(self) -> dict[str, object]:
        """Sayaçların anlık görüntüsü (kimlik başına istek + dakikalık hız)."""
        with self._lock:
            requests = dict(self._requests)
            rate_limited = self._rate_limited
        uptime = max(time.monotonic() - self.started_at, 0.0)
        minutes = uptime / 60.0
        by_identity = {
            identity: {
                "requests": count,
                "rate_per_min": round(count / minutes, 3) if minutes else 0.0,
            }
            for identity, count in sorted(requests.items(), key=lambda item: -item[1])
        }
        return {
            "uptime_seconds": round(uptime, 3),
            "requests_total": sum(requests.values()),
            "rate_limited_total": rate_limited,
            "distinct_identities": len(requests),
            "by_identity": by_identity,
        }
