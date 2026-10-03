"""Uygulama ayarları.

Kural: güvensiz varsayılan sır **yok**. `JWT_SECRET_KEY` verilmezse rastgele anahtar üretilir ve
uyarı basılır (bilinen sabit varsayılan, token sahteleme açığıdır).
"""

from __future__ import annotations

import os
import secrets
import warnings
from dataclasses import dataclass, field

DEFAULT_CORS: tuple[str, ...] = ("http://localhost:8000", "http://127.0.0.1:8000", "null")


@dataclass(frozen=True)
class Settings:
    db_path: str = "fairplay.db"
    jwt_secret: str = field(default_factory=lambda: secrets.token_urlsafe(32))
    jwt_ttl_minutes: int = 720
    cors_origins: tuple[str, ...] = DEFAULT_CORS
    energy_max: int = 100
    energy_per_wager: int = 10
    energy_per_hour: str = "10"
    risk_of_ruin_threshold: str = "0.15"

    @classmethod
    def from_env(cls) -> Settings:
        origins = tuple(
            origin.strip() for origin in os.getenv("CORS_ORIGINS", "").split(",") if origin.strip()
        )
        secret = os.getenv("JWT_SECRET_KEY", "")
        if not secret:
            warnings.warn(
                "JWT_SECRET_KEY tanımlı değil; rastgele anahtar üretildi. "
                "Yeniden başlatmada mevcut token'lar geçersiz olur.",
                stacklevel=2,
            )
        return cls(
            db_path=os.getenv("DATABASE_PATH", "fairplay.db"),
            jwt_secret=secret or secrets.token_urlsafe(32),
            cors_origins=origins or DEFAULT_CORS,
        )
