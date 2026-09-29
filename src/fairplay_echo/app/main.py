"""FastAPI uygulama fabrikası — tek süreç, thin shell.

HTTP kodları **tek yerde** verilir: alan/servis hataları burada duruma çevrilir, servis katmanı
web çatısını tanımaz (bkz. `AGENTS.md` §2).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from dataclasses import replace
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from .. import __version__
from ..core.errors import (
    AlreadySettled,
    DomainError,
    DuplicateWager,
    InsufficientCash,
    InvalidAmount,
    UnknownWager,
)
from .api import router
from .clock import Clock, SystemClock
from .config import Settings
from .errors import AppError

Handler = Callable[[Request, Exception], Awaitable[JSONResponse]]

_CORE_STATUS: dict[type[DomainError], int] = {
    InsufficientCash: 400,
    InvalidAmount: 400,
    UnknownWager: 404,
    AlreadySettled: 409,
    DuplicateWager: 409,
}


def _error_handler(status_code: int) -> Handler:
    async def handler(_request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=status_code, content={"detail": str(exc)})

    return handler


_VALIDATION_FALLBACK: dict[str, str] = {
    "missing": "zorunlu alan",
    "greater_than": "izin verilen aralığın dışında",
    "less_than": "izin verilen aralığın dışında",
    "value_error": "geçersiz değer",
    "decimal_parsing": "sayı değil",
    "int_parsing": "tam sayı değil",
    "float_parsing": "sayı değil",
}


def _humanize(error: Mapping[str, object]) -> str:
    """Pydantic hatasını insan okur Türkçe bir ifadeye çevirir."""
    kind = str(error.get("type", ""))
    context = error.get("ctx") or {}
    if kind == "string_too_short" and isinstance(context, dict) and "min_length" in context:
        return f"en az {context['min_length']} karakter olmalı"
    if kind == "string_too_long" and isinstance(context, dict) and "max_length" in context:
        return f"en fazla {context['max_length']} karakter olmalı"
    return _VALIDATION_FALLBACK.get(kind, str(error.get("msg", "geçersiz")))


def create_app(
    *,
    db_path: str | None = None,
    settings: Settings | None = None,
    clock: Clock | None = None,
) -> FastAPI:
    resolved = settings or Settings.from_env()
    if db_path is not None:
        resolved = replace(resolved, db_path=db_path)

    app = FastAPI(title="FairPlay Echo API", version=__version__)
    app.state.settings = resolved
    app.state.clock = clock or SystemClock()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(resolved.cors_origins),
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)

    async def app_error(_request: Request, exc: Exception) -> JSONResponse:
        detail = exc.detail if isinstance(exc, AppError) else str(exc)
        status_code = exc.status_code if isinstance(exc, AppError) else 400
        return JSONResponse(status_code=status_code, content={"detail": detail})

    async def validation_error(_request: Request, exc: Exception) -> JSONResponse:
        """Doğrulama hatası insan okur bir cümle olarak döner — ham Python repr'i DEĞİL."""
        detail = "Gönderilen alanlar geçersiz."
        if isinstance(exc, RequestValidationError):
            parts: list[str] = []
            for error in exc.errors():
                location = ".".join(str(item) for item in error.get("loc", ()) if item != "body")
                parts.append(f"{location or 'alan'}: {_humanize(error)}")
            if parts:
                detail = "Doğrulama hatası → " + "; ".join(parts)
        return JSONResponse(status_code=400, content={"detail": detail})

    app.add_exception_handler(AppError, app_error)
    for error_type, status_code in _CORE_STATUS.items():
        app.add_exception_handler(error_type, _error_handler(status_code))
    app.add_exception_handler(RequestValidationError, validation_error)

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    @app.get("/")
    def root() -> object:
        page = Path(__file__).resolve().parents[1] / "web" / "index.html"
        if page.exists():
            return FileResponse(page)
        return {"service": "fairplay-echo", "version": __version__}

    return app
