"""Doküman iddiaları ↔ gerçek kod — drift kalkanı (P11).

Bu testler yeşil değilse iş bitmemiştir: `docs/` ile kod arasında sapma var demektir.
"""

from __future__ import annotations

import re
from pathlib import Path

from fairplay_echo.app.config import Settings
from fairplay_echo.app.main import create_app
from fairplay_echo.cli import render_api_docs

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SRC = ROOT / "src" / "fairplay_echo"
GOLDEN_TEST = ROOT / "tests" / "golden" / "test_spec_examples.py"
PROPERTY_TEST = ROOT / "tests" / "property" / "test_invariants.py"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _golden_ids(text: str) -> set[str]:
    return set(re.findall(r"\[(G-\d+)\]", text))


def test_every_spec_example_has_a_golden_test() -> None:
    spec = _golden_ids(_read(DOCS / "20-accounting-spec.md"))
    tests = _golden_ids(_read(GOLDEN_TEST))
    assert spec, "Spec'te hiç [G-x] örneği bulunamadı."
    assert spec == tests, f"Spec ↔ golden test farkı: {sorted(spec ^ tests)}"


def test_every_invariant_has_a_property_test() -> None:
    documented = set(re.findall(r"\bI[1-6]\b", _read(DOCS / "10-domain-model.md")))
    tested = set(re.findall(r"\bI[1-6]\b", _read(PROPERTY_TEST)))
    missing = documented - tested
    assert not missing, f"Testi olmayan değişmez: {sorted(missing)}"


def test_documented_core_modules_exist() -> None:
    listed = set(re.findall(r"^ {2}([a-z_]+)\.py\b", _read(DOCS / "30-architecture.md"), re.M))
    actual = {p.stem for p in (SRC / "core").glob("*.py") if p.stem != "__init__"}
    assert listed, "docs/30-architecture.md'de core modül listesi bulunamadı."
    assert listed == actual, f"Belge ↔ gerçek modül farkı: {sorted(listed ^ actual)}"


def test_python_requirement_matches_documented_version() -> None:
    pyproject = _read(ROOT / "pyproject.toml")
    requires = re.search(r'requires-python\s*=\s*">=([\d.]+)"', pyproject)
    assert requires is not None, "pyproject.toml'da requires-python yok."
    version = requires.group(1)
    adr = _read(DOCS / "60-decisions" / "0001-stack.md")
    assert f"Python {version}+" in adr, f"ADR-0001 'Python {version}+' demiyor (gerçek: {version})."


def test_generated_api_docs_are_current() -> None:
    """`docs/40-api.md` üreticinin çıktısıyla **birebir** aynı olmalı.

    Not: rota listesi `app.routes` üzerinden okunmaz — FastAPI 0.142'de `include_router`
    rotaları kopyalamıyor, bir `_IncludedRouter` sarmalayıcısı ekliyor; iç yapıya bağlanmak
    kırılgan olurdu. Doğru kontrol, dosyanın **üretici çıktısıyla** karşılaştırılmasıdır.
    """
    app = create_app(db_path=":memory:", settings=Settings(jwt_secret="docs-sync-only-secret"))
    expected = render_api_docs(app.openapi())
    actual = _read(DOCS / "40-api.md")
    assert actual == expected, (
        "docs/40-api.md bayat: `python -m fairplay_echo.cli render-api-docs` ile yeniden üret."
    )


def test_documented_endpoints_cover_every_schema_path() -> None:
    """Belgedeki her uç OpenAPI şemasında gerçekten var olmalı ve tersi."""
    app = create_app(db_path=":memory:", settings=Settings(jwt_secret="docs-sync-only-secret"))
    paths = app.openapi()["paths"]
    assert isinstance(paths, dict)
    schema = {
        (method.upper(), path)
        for path, operations in paths.items()
        for method in operations
    }
    documented = set(
        re.findall(r"^\| ([A-Z]+) \| `([^`]+)` \|", _read(DOCS / "40-api.md"), re.M)
    )
    assert documented == schema, f"Belge ↔ şema farkı: {sorted(documented ^ schema)}"


def test_client_side_settlement_endpoint_is_gone() -> None:
    """Güven sınırı belgede de görünür olmalı: istemci sonuç bildiren uç yoktur."""
    assert "/api/wager/settle" not in _read(DOCS / "40-api.md")


def test_documented_test_paths_exist() -> None:
    listed = set(re.findall(r"`(tests/[A-Za-z0-9_/\.]+)`", _read(DOCS / "50-test-strategy.md")))
    assert listed, "docs/50-test-strategy.md'de test yolu listesi bulunamadı."
    missing = {path for path in listed if not (ROOT / path).exists()}
    assert not missing, f"Belgede yazan ama var olmayan test yolu: {sorted(missing)}"
