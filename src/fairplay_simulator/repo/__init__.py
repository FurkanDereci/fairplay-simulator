"""Kalıcılık katmanı.

Defter **tek gerçek kaynaktır**; şema ondan türetilir (ADR-0002). Kupon meta verisi ayrı
tabloda tutulur ama kuponun **durumu** (bekleyen/sonuçlanmış) yine defterden türetilir —
ayrı bir `status` kolonu tutulmaz.
"""

from .sqlite_repo import Repository, UserRecord, WagerRecord

__all__ = ["Repository", "UserRecord", "WagerRecord"]
