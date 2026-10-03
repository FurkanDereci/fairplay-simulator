"""Kimlik doğrulama: parola özeti (stdlib `scrypt`) ve HS256 JWT."""

from __future__ import annotations

import hashlib
import hmac
import os
from datetime import datetime, timedelta

import jwt

_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_DKLEN = 32
_ALGORITHM = "HS256"


def _scrypt(password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=_DKLEN,
    )


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    return f"scrypt${salt.hex()}${_scrypt(password, salt).hex()}"


def verify_password(password: str, encoded: str) -> bool:
    parts = encoded.split("$")
    if len(parts) != 3 or parts[0] != "scrypt":
        return False
    _, salt_hex, digest_hex = parts
    try:
        salt = bytes.fromhex(salt_hex)
    except ValueError:
        return False
    return hmac.compare_digest(_scrypt(password, salt).hex(), digest_hex)


def create_token(
    *, user_id: str, username: str, secret: str, ttl_minutes: int, now: datetime
) -> str:
    payload = {
        "sub": user_id,
        "username": username,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=ttl_minutes)).timestamp()),
    }
    return jwt.encode(payload, secret, algorithm=_ALGORITHM)


def decode_token(token: str, secret: str, *, now: datetime) -> dict[str, object] | None:
    """Token'ı çözer ve süresini **enjekte edilen saatle** doğrular.

    Süre kontrolü elle yapılır: PyJWT `exp`'i duvar saatine göre doğruluyor ve `current_time`
    geçersiz kılma yolu 3.0'da kaldırılıyor. Saat otoritesi bizde kalmalı (determinizm), o yüzden
    `exp` doğrulaması kapatılıp yerine kendi kontrolümüz konur.
    """
    try:
        payload = jwt.decode(token, secret, algorithms=[_ALGORITHM], options={"verify_exp": False})
    except jwt.PyJWTError:
        return None
    if not isinstance(payload, dict):
        return None
    expires_at = payload.get("exp")
    if isinstance(expires_at, (int, float)) and now.timestamp() >= float(expires_at):
        return None
    return payload
