"""S3 — kalıcılık ve replay.

DoD: defterden okunan kayıtlar, bellekteki artımlı durumun **birebir aynısını** üretir (I2)
ve para değerleri tam (yuvarlama kaybı yok) hayatta kalır.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date
from decimal import Decimal as D
from pathlib import Path

import pytest

from fairplay_simulator.cli import main
from fairplay_simulator.core.cooldown import CooldownState
from fairplay_simulator.core.ledger import Ledger
from fairplay_simulator.core.nav import Fund
from fairplay_simulator.repo import Repository

#: Göç öncesi `cooldown_state` şeması (ADR-0015): `last_solvent_day` kolonu **yok**.
_LEGACY_COOLDOWN_TABLE = """
CREATE TABLE cooldown_state (
    user_id        TEXT PRIMARY KEY REFERENCES users(id),
    tier           INTEGER NOT NULL,
    solvent_streak INTEGER NOT NULL,
    locked_until   TEXT
);
"""


def _seeded_ledger() -> Ledger:
    ledger = Ledger()
    ledger.deposit(D("1000"))
    ledger.place_wager("w1", D("100"))
    ledger.settle_wager("w1", D("100"), D("250"))
    ledger.refill(D("1000"))
    ledger.place_wager("w2", D("333.33"))
    return ledger


def test_replay_from_db_matches_memory(tmp_path: Path) -> None:
    """I2 — kalıcılık üzerinden replay, bellekteki projeksiyonla birebir aynı."""
    ledger = _seeded_ledger()
    live = Fund()
    for entry in ledger.entries:
        live.apply(entry)

    with Repository(tmp_path / "test.db") as repo:
        user = repo.create_user("aytek", "a@example.com", "hash")
        repo.append_entries(user.id, ledger.entries)
        restored = Fund.replay(repo.entries(user.id))

    assert restored.cash == live.cash
    assert restored.locked == live.locked
    assert restored.units == live.units
    assert restored.nav == live.nav
    assert restored.twr == live.twr
    assert restored.open_wagers == live.open_wagers
    assert restored.settled_wagers == live.settled_wagers


def test_money_survives_roundtrip_exactly(tmp_path: Path) -> None:
    """Para TEXT olarak saklanır: 28 basamaklı birim değeri kayıpsız döner."""
    ledger = _seeded_ledger()
    with Repository(tmp_path / "test.db") as repo:
        user = repo.create_user("aytek", "a@example.com", "hash")
        repo.append_entries(user.id, ledger.entries)
        entries = repo.entries(user.id)

    restored = Fund.replay(entries)
    assert restored.units == Fund.replay(ledger.entries).units
    assert len(str(restored.units)) > 20  # tam hassasiyet korundu
    assert restored.nav == D("115.0000")


def test_wager_metadata_and_closing_odds(tmp_path: Path) -> None:
    with Repository(tmp_path / "test.db") as repo:
        user = repo.create_user("aytek", "a@example.com", "hash")
        repo.save_wager(
            wager_id="w1",
            user_id=user.id,
            match_id="m1",
            match_title="A vs B",
            market_type="1X2",
            selection="HOME",
            odds=D("1.95"),
        )
        assert repo.wager("w1") is not None
        assert repo.wagers_for(user.id, match_id="m1")[0].selection == "HOME"
        assert repo.wagers_for(user.id, match_id="m2") == []

        repo.set_closing_odds("w1", D("1.80"))
        record = repo.wager("w1")
        assert record is not None
        assert record.closing_odds == D("1.80")


def test_policy_state_roundtrip(tmp_path: Path) -> None:
    from datetime import datetime, timezone

    moment = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    with Repository(tmp_path / "test.db", clock=lambda: moment) as repo:
        user = repo.create_user("aytek", "a@example.com", "hash")
        assert repo.energy(user.id) is None
        repo.save_energy(user.id, 40, moment)
        assert repo.energy(user.id) == (40, moment)

        state = CooldownState(tier=2, solvent_streak=1, locked_until=moment)
        repo.save_cooldown(user.id, state)
        assert repo.cooldown(user.id) == state


def test_cli_replay_prints_projection(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    db = tmp_path / "cli.db"
    ledger = _seeded_ledger()
    with Repository(db) as repo:
        user = repo.create_user("aytek", "a@example.com", "hash")
        repo.append_entries(user.id, ledger.entries)

    assert main(["replay", "aytek", "--db", str(db)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["entries"] == len(ledger.entries)
    assert payload["open_wagers"] == {"w2": "333.33"}

    assert main(["replay", "yok-boyle", "--db", str(db)]) == 1


def test_existing_db_gets_the_solvent_day_column(tmp_path: Path) -> None:
    """Göç (ADR-0015): eski şemalı dosya açılınca kolon **eklenir** ve çalışır.

    `CREATE TABLE IF NOT EXISTS` var olan tabloyu değiştirmez; göç olmasaydı `save_cooldown`
    yeni kolona yazamaz, yani eski kullanıcıların verisi okunamaz hâle gelirdi.
    """
    path = tmp_path / "eski.db"
    legacy = sqlite3.connect(str(path))
    legacy.executescript(_LEGACY_COOLDOWN_TABLE)
    legacy.commit()
    legacy.close()

    with Repository(path) as repo:
        user = repo.create_user("aytek", "aytek@example.com", "hash")
        repo.save_cooldown(user.id, CooldownState(tier=2, last_solvent_day=date(2026, 1, 1)))
        assert repo.cooldown(user.id).last_solvent_day == date(2026, 1, 1)


def test_migration_is_idempotent(tmp_path: Path) -> None:
    """Göç tekrar açılışta yeniden uygulanmaz (kolon zaten var) ve veri korunur."""
    path = tmp_path / "tekrar.db"
    with Repository(path) as repo:
        user = repo.create_user("aytek", "aytek@example.com", "hash")
        repo.save_cooldown(user.id, CooldownState(tier=1, last_solvent_day=date(2026, 2, 2)))

    with Repository(path) as repo:
        assert repo.cooldown(repo.user_by_username("aytek").id).last_solvent_day == date(2026, 2, 2)
