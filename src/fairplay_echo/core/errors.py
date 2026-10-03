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


class UnsupportedLedgerVersion(DomainError):
    """Defter/veritabanı şema sürümü kodun tanımadığı bir sürüm.

    Sessizce okumak yerine **açıkça** durur: eski sürüm upcaster ister, yeni sürüm kod güncellemesi.
    """


class InvalidOdds(DomainError):
    """Oran dizisi bozuk: eksik sonuç, `O ≤ 1` ya da negatif vig (overround ≤ 0).

    Girdi **reddedilir**, kırpılmaz: bozuk beslemeyi gizlemek (spec §5'teki `max(0, …)` sınıfı)
    onu kabul etmekten kötüdür (`docs/70` §7.2, Suite 3).
    """
