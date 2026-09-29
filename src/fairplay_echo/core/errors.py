"""Alan hataları — istisna hiyerarşisi.

Servis katmanı bu istisnaları HTTP durum kodlarına çevirir (`docs/10-domain-model.md` §4).
"""

from __future__ import annotations


class DomainError(Exception):
    """Tüm alan hatalarının ortak atası."""


class InvalidAmount(DomainError):
    """Tutar sıfır, negatif veya tutarsız."""


class InsufficientCash(DomainError):
    """Kasa bu bahsi karşılayamaz."""


class UnknownWager(DomainError):
    """Kupon fonun açık kuponlarında yok."""


class AlreadySettled(DomainError):
    """Kupon zaten sonuçlanmış (idempotentlik: I3)."""


class DuplicateWager(DomainError):
    """Aynı kimlikli kupon ikinci kez açılmak istendi."""
