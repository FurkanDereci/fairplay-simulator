"""Defter biçimi: sürüm kapısı ve **donmuş kayıt** testi.

Neden var: event-sourced bir defterde en sessiz tehlike, kayıt biçiminin değişip eski
kayıtların **yanlış** okunmasıdır. Donmuş fixture o sınıfı kapatır: biçim/ semantics
değişirse test kırmızıya düşer, sessizce yanlış durum üretilemez.
"""

from __future__ import annotations

import json
import sqlite3
from decimal import Decimal as D
from pathlib import Path

import pytest

from fairplay_simulator.core.errors import UnsupportedLedgerVersion
from fairplay_simulator.core.ledger import (
    LEDGER_SCHEMA_VERSION,
    Ledger,
    decode_ledger,
    encode_ledger,
)
from fairplay_simulator.core.money import q_nav, q_units
from fairplay_simulator.core.nav import Fund
from fairplay_simulator.repo import Repository

FIXTURE = Path(__file__).resolve().parents[1] / "data" / "ledger_v1.json"


def _fixture_payload() -> dict[str, object]:
    loaded = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def test_frozen_ledger_still_replays_to_the_same_state() -> None:
    """Donmuş v1 kaydı, `[G-1]` senaryosunun aynı durumunu üretmeli."""
    entries = decode_ledger(_fixture_payload())
    assert len(entries) == 4

    fund = Fund.replay(entries)
    assert q_nav(fund.nav) == D("115.0000")
    assert q_units(fund.units) == D("18.6956522")
    assert fund.twr == D("15.00")
    assert fund.settled_wagers == {"w1"}
    assert fund.open_wagers == {}


def test_ledger_round_trips_through_its_own_format() -> None:
    ledger = Ledger()
    ledger.deposit(D("1000"))
    ledger.place_wager("w1", D("100"))
    ledger.settle_wager("w1", D("100"), D("250"))

    payload = encode_ledger(ledger.entries)
    assert payload["schema_version"] == LEDGER_SCHEMA_VERSION
    assert decode_ledger(payload) == list(ledger.entries)


def test_unknown_schema_version_is_refused_not_misread() -> None:
    """Bilinmeyen sürüm sessizce okunmaz: açık hata döner (upcaster/kod güncellemesi ister)."""
    stale = _fixture_payload() | {"schema_version": LEDGER_SCHEMA_VERSION + 1}
    with pytest.raises(UnsupportedLedgerVersion):
        decode_ledger(stale)

    broken = {"schema_version": LEDGER_SCHEMA_VERSION}
    with pytest.raises(UnsupportedLedgerVersion):
        decode_ledger(broken)


def test_database_is_stamped_with_the_ledger_version(tmp_path: Path) -> None:
    with Repository(tmp_path / "v.db") as repo:
        assert repo.schema_version() == LEDGER_SCHEMA_VERSION


def test_a_newer_database_is_refused(tmp_path: Path) -> None:
    """Kodun tanımadığı (daha yeni) bir dosya açılmaz — sessiz yanlış okuma olmaz."""
    path = tmp_path / "newer.db"
    with Repository(path) as repo:
        assert repo.schema_version() == LEDGER_SCHEMA_VERSION
    connection = sqlite3.connect(str(path))
    try:
        connection.execute(f"PRAGMA user_version = {LEDGER_SCHEMA_VERSION + 1}")
        connection.commit()
    finally:
        connection.close()

    with pytest.raises(UnsupportedLedgerVersion):
        Repository(path)
