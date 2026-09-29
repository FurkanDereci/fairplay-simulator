"""Saf alan çekirdeği.

Bu paket framework, veritabanı, saat veya rastgelelik **import etmez**.
Zaman ve rastgelelik çağıran tarafından enjekte edilir (bkz. `AGENTS.md` §3).
"""

from .errors import (
    AlreadySettled,
    DomainError,
    DuplicateWager,
    InsufficientCash,
    InvalidAmount,
    UnknownWager,
)

__all__ = [
    "AlreadySettled",
    "DomainError",
    "DuplicateWager",
    "InsufficientCash",
    "InvalidAmount",
    "UnknownWager",
]
