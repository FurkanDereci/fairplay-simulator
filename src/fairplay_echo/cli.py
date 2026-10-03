"""Komut satırı arayüzü.

`replay` bir kullanıcının defterini oynatıp projeksiyonu basar — bir hata raporunu
`replay` edilebilir hale getirir (I2).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from types import ModuleType
from typing import Any

from . import __version__
from .core.nav import Fund
from .repo import Repository


def _resolve_user_id(repo: Repository, key: str) -> str | None:
    user = repo.user_by_id(key) or repo.user_by_username(key)
    return user.id if user is not None else None


def _cmd_replay(args: argparse.Namespace) -> int:
    with Repository(args.db) as repo:
        user_id = _resolve_user_id(repo, args.user)
        if user_id is None:
            print(f"Kullanıcı bulunamadı: {args.user}", file=sys.stderr)
            return 1

        entries = repo.entries(user_id)
        fund = Fund.replay(entries)
        payload = {
            "user_id": user_id,
            "entries": len(entries),
            "series_id": fund.series_id,
            "cash": str(fund.cash),
            "locked": str(fund.locked),
            "total_value": str(fund.total_value),
            "units": str(fund.units),
            "nav": str(fund.nav),
            "twr_pct": str(fund.twr),
            "closed": fund.closed,
            "open_wagers": {key: str(value) for key, value in sorted(fund.open_wagers.items())},
            "settled_wagers": sorted(fund.settled_wagers),
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def _cmd_version(_args: argparse.Namespace) -> int:
    print(f"fairplay-echo {__version__}")
    return 0


def _app_module() -> ModuleType:
    """Web yığınını yalnız gerektiğinde yükler; CLI'nin geri kalanı hafif kalır."""
    import importlib

    return importlib.import_module("fairplay_echo.app.main")


def _docs_only_app(db_path: str) -> Any:
    """Şema/doküman üretimi için uygulama — gerçek sır istemez, uyarı basmaz."""
    import importlib

    app_module = _app_module()
    config_module = importlib.import_module("fairplay_echo.app.config")
    settings = config_module.Settings(jwt_secret="openapi-render-only-secret")
    return app_module.create_app(db_path=db_path, settings=settings)


def _cmd_serve(args: argparse.Namespace) -> int:
    import importlib

    uvicorn = importlib.import_module("uvicorn")
    app_module = _app_module()
    uvicorn.run(app_module.create_app(db_path=args.db), host=args.host, port=args.port)
    return 0


def _cmd_export_openapi(args: argparse.Namespace) -> int:
    app = _docs_only_app(args.db)
    print(json.dumps(app.openapi(), ensure_ascii=False, indent=2))
    return 0


def render_api_docs(spec: dict[str, object]) -> str:
    paths = spec.get("paths")
    assert isinstance(paths, dict)
    rows: list[tuple[str, str, str]] = []
    for path, operations in paths.items():
        assert isinstance(operations, dict)
        for method, operation in operations.items():
            summary = ""
            if isinstance(operation, dict):
                raw = operation.get("summary") or operation.get("description") or ""
                summary = str(raw).splitlines()[0] if raw else ""
            rows.append((str(method).upper(), path, summary))
    rows.sort(key=lambda row: (row[1], row[0]))

    lines = [
        "# API Referansı",
        "",
        "> **Bu dosya elle yazılmaz.** OpenAPI şemasından üretilir; şema uygulamadan türetildiği",
        "> için belge ile kod arasında sapma oluşamaz (P11).",
        ">",
        "> Üretim: `python -m fairplay_echo.cli render-api-docs --output docs/40-api.md`",
        "",
        f"Toplam **{len(rows)} uç**.",
        "",
        "| Metot | Yol | Özet |",
        "| --- | --- | --- |",
    ]
    lines.extend(f"| {method} | `{path}` | {summary} |" for method, path, summary in rows)
    lines.append("")
    return "\n".join(lines)


def _cmd_render_api_docs(args: argparse.Namespace) -> int:
    app = _docs_only_app(":memory:")
    rendered = render_api_docs(app.openapi())
    if args.output == "-":
        print(rendered)
    else:
        Path(args.output).write_text(rendered, encoding="utf-8")
        print(f"yazıldı: {args.output} ({rendered.count(chr(10))} satır)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fairplay-echo", description="FairPlay Echo")
    sub = parser.add_subparsers(dest="command", required=True)

    replay = sub.add_parser("replay", help="Bir kullanıcının defterini oynat ve durumu bas")
    replay.add_argument("user", help="kullanıcı adı veya id")
    replay.add_argument("--db", default="fairplay.db", help="SQLite dosyası")
    replay.set_defaults(func=_cmd_replay)

    serve = sub.add_parser("serve", help="API sunucusunu çalıştır")
    serve.add_argument("--db", default="fairplay.db", help="SQLite dosyası")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    serve.set_defaults(func=_cmd_serve)

    version = sub.add_parser("version", help="Sürümü bas")
    version.set_defaults(func=_cmd_version)

    openapi = sub.add_parser("export-openapi", help="OpenAPI şemasını JSON olarak bas")
    openapi.add_argument("--db", default="fairplay.db")
    openapi.set_defaults(func=_cmd_export_openapi)

    render = sub.add_parser("render-api-docs", help="OpenAPI'den docs/40-api.md üret")
    render.add_argument("--output", default="docs/40-api.md")
    render.set_defaults(func=_cmd_render_api_docs)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result: int = args.func(args)
    return result


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
