"""FastAPI bağımlılıkları: ayar, saat, depo ve servis enjeksiyonu."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Header, Request

from ..repo import Repository, UserRecord
from .clock import Clock
from .config import Settings
from .errors import Unauthorized
from .services import PortfolioService


def get_settings(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


def get_clock(request: Request) -> Clock:
    clock: Clock = request.app.state.clock
    return clock


def get_repo(request: Request) -> Iterator[Repository]:
    """İstek başına bağlantı: SQLite tek dosya, eşzamanlı istekler güvenli kalsın."""
    repo = Repository(request.app.state.settings.db_path)
    try:
        yield repo
    finally:
        repo.close()


def get_service(
    repo: Repository = Depends(get_repo),
    settings: Settings = Depends(get_settings),
    clock: Clock = Depends(get_clock),
) -> PortfolioService:
    return PortfolioService(repo, settings, clock)


def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    service: PortfolioService = Depends(get_service),
) -> UserRecord:
    if not authorization or not authorization.startswith("Bearer "):
        raise Unauthorized("Authorization: Bearer <token> başlığı gerekli.")
    return service.user_from_token(authorization.removeprefix("Bearer ").strip())
