"""SQLite kalıcılığı.

Para kolonları **TEXT** (Decimal tam temsil için); durum defterden **türetilir**, kolondan okunmaz.
Şema S3 diliminde bu dosyada tanımlıdır; göç (migration) ihtiyacı doğana kadar tek dosya yeter.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from ..core.cooldown import CooldownState
from ..core.errors import UnsupportedLedgerVersion
from ..core.ledger import LEDGER_SCHEMA_VERSION, EntryType, LedgerEntry
from ..core.money import Money
from ..engines.match import MatchRecord

Clock = Callable[[], datetime]

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            TEXT PRIMARY KEY,
    username      TEXT NOT NULL UNIQUE,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ledger_entries (
    seq        INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    TEXT NOT NULL REFERENCES users(id),
    entry_type TEXT NOT NULL,
    amount     TEXT NOT NULL,
    stake      TEXT NOT NULL,
    wager_id   TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ledger_user ON ledger_entries (user_id, seq);

CREATE TABLE IF NOT EXISTS wagers (
    wager_id     TEXT PRIMARY KEY,
    user_id      TEXT NOT NULL REFERENCES users(id),
    match_id     TEXT NOT NULL,
    match_title  TEXT NOT NULL,
    market_type  TEXT NOT NULL,
    selection    TEXT NOT NULL,
    odds         TEXT NOT NULL,
    closing_odds TEXT,
    placed_at    TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_wagers_user ON wagers (user_id, match_id);

CREATE TABLE IF NOT EXISTS energy_state (
    user_id     TEXT PRIMARY KEY REFERENCES users(id),
    energy      INTEGER NOT NULL,
    last_update TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cooldown_state (
    user_id        TEXT PRIMARY KEY REFERENCES users(id),
    tier           INTEGER NOT NULL,
    solvent_streak INTEGER NOT NULL,
    locked_until   TEXT
);

CREATE TABLE IF NOT EXISTS matches (
    match_id   TEXT PRIMARY KEY,
    home_team  TEXT NOT NULL,
    away_team  TEXT NOT NULL,
    home_score INTEGER NOT NULL,
    away_score INTEGER NOT NULL,
    odds_1x2   TEXT NOT NULL,
    seed       INTEGER,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS idempotency (
    user_id    TEXT NOT NULL,
    key        TEXT NOT NULL,
    response   TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (user_id, key)
);
"""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _parse_dt(value: str | None) -> datetime | None:
    if value is None:
        return None
    parsed = datetime.fromisoformat(value)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


@dataclass(frozen=True)
class UserRecord:
    id: str
    username: str
    email: str
    password_hash: str


@dataclass(frozen=True)
class WagerRecord:
    wager_id: str
    user_id: str
    match_id: str
    match_title: str
    market_type: str
    selection: str
    odds: Money
    closing_odds: Money | None
    placed_at: datetime


class Repository:
    """Tek süreç + SQLite varsayımıyla çalışan ince depo."""

    def __init__(self, path: str | Path, *, clock: Clock | None = None) -> None:
        self.path = str(path)
        self._clock: Clock = clock or _utcnow
        self._conn = sqlite3.connect(self.path)
        self._conn.row_factory = sqlite3.Row
        # WAL: okuma/yazma çakışmasını azaltır (istek başına bağlantı açıyoruz).
        # synchronous=NORMAL: tutarlılık korunur; bedeli, elektrik kesintisinde son commit'in
        # geri alınabilmesidir (bkz. ADR-0008 — bilinçli karar, varsayılana bırakılmadı).
        # foreign_keys: SQLite kısıtları varsayılan olarak UYGULAMAZ; açıkça açılmalı.
        self._conn.execute("PRAGMA journal_mode = WAL")
        self._conn.execute("PRAGMA synchronous = NORMAL")
        self._conn.execute("PRAGMA foreign_keys = ON")
        # Defter şeması sürümü dosyaya damgalanır: koddan **yeni** bir dosya sessizce okunmaz.
        stored_version = self.schema_version()
        if stored_version > LEDGER_SCHEMA_VERSION:
            raise UnsupportedLedgerVersion(
                f"Veritabanı defter sürümü {stored_version}, bu kod {LEDGER_SCHEMA_VERSION} — "
                "dosya koddan yeni; kodu güncelle (ADR-0009)."
            )
        self._conn.execute(f"PRAGMA user_version = {LEDGER_SCHEMA_VERSION}")
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def schema_version(self) -> int:
        """Dosyaya damgalanmış defter şema sürümü (SQLite `user_version`)."""
        return int(self._conn.execute("PRAGMA user_version").fetchone()[0])

    def backup_to(self, target: str | Path) -> Path:
        """Tutarlı yedek: **online backup API**'si (WAL'da düz dosya kopyası yırtılır).

        Yedeğin gerçekten kurtarılabilir olduğu `tests/repo` içindeki geri yükleme
        tatbikatıyla kanıtlanır — `integrity_check` geçmesi bunu kanıtlamaz.
        """
        destination = sqlite3.connect(str(target))
        try:
            self._conn.backup(destination)
            destination.commit()
        finally:
            destination.close()
        return Path(target)

    def close(self) -> None:
        self._conn.close()

    def journal_mode(self) -> str:
        """Etkin journal modu (`wal`/`delete`/`memory`) — karar testle doğrulanabilsin."""
        return str(self._conn.execute("PRAGMA journal_mode").fetchone()[0]).lower()

    def synchronous(self) -> int:
        """Etkin `synchronous` seviyesi (0=OFF, 1=NORMAL, 2=FULL, 3=EXTRA)."""
        return int(self._conn.execute("PRAGMA synchronous").fetchone()[0])

    def foreign_keys_enabled(self) -> bool:
        """Yabancı anahtar zorlaması açık mı (SQLite'ta varsayılan KAPALI)."""
        return bool(self._conn.execute("PRAGMA foreign_keys").fetchone()[0])

    def __enter__(self) -> Repository:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # --- kullanıcılar -------------------------------------------------------
    def create_user(self, username: str, email: str, password_hash: str) -> UserRecord:
        user_id = str(uuid.uuid4())
        self._conn.execute(
            "INSERT INTO users (id, username, email, password_hash, created_at)"
            " VALUES (?, ?, ?, ?, ?)",
            (user_id, username, email, password_hash, _iso(self._clock())),
        )
        self._conn.commit()
        return UserRecord(user_id, username, email, password_hash)

    def user_by_username(self, username: str) -> UserRecord | None:
        row = self._conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        return self._user(row)

    def user_by_id(self, user_id: str) -> UserRecord | None:
        row = self._conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return self._user(row)

    @staticmethod
    def _user(row: sqlite3.Row | None) -> UserRecord | None:
        if row is None:
            return None
        return UserRecord(row["id"], row["username"], row["email"], row["password_hash"])

    # --- defter -------------------------------------------------------------
    def append_entry(self, user_id: str, entry: LedgerEntry) -> None:
        self._conn.execute(
            "INSERT INTO ledger_entries (user_id, entry_type, amount, stake, wager_id, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (
                user_id,
                entry.entry_type.value,
                str(entry.amount),
                str(entry.stake),
                entry.wager_id,
                _iso(self._clock()),
            ),
        )
        self._conn.commit()

    def append_entries(self, user_id: str, entries: Sequence[LedgerEntry]) -> None:
        self._conn.executemany(
            "INSERT INTO ledger_entries (user_id, entry_type, amount, stake, wager_id, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            [
                (
                    user_id,
                    e.entry_type.value,
                    str(e.amount),
                    str(e.stake),
                    e.wager_id,
                    _iso(self._clock()),
                )
                for e in entries
            ],
        )
        self._conn.commit()

    def entries(self, user_id: str) -> list[LedgerEntry]:
        rows = self._conn.execute(
            "SELECT seq, entry_type, amount, stake, wager_id FROM ledger_entries"
            " WHERE user_id = ? ORDER BY seq",
            (user_id,),
        ).fetchall()
        return [
            LedgerEntry(
                seq=row["seq"],
                entry_type=EntryType(row["entry_type"]),
                amount=Decimal(row["amount"]),
                stake=Decimal(row["stake"]),
                wager_id=row["wager_id"],
            )
            for row in rows
        ]

    # --- kupon meta verisi ---------------------------------------------------
    def save_wager(
        self,
        *,
        wager_id: str,
        user_id: str,
        match_id: str,
        match_title: str,
        market_type: str,
        selection: str,
        odds: Money,
    ) -> None:
        self._conn.execute(
            "INSERT INTO wagers (wager_id, user_id, match_id, match_title, market_type,"
            " selection, odds, closing_odds, placed_at) VALUES (?, ?, ?, ?, ?, ?, ?, NULL, ?)",
            (
                wager_id,
                user_id,
                match_id,
                match_title,
                market_type,
                selection,
                str(odds),
                _iso(self._clock()),
            ),
        )
        self._conn.commit()

    def wager(self, wager_id: str) -> WagerRecord | None:
        row = self._conn.execute(
            "SELECT * FROM wagers WHERE wager_id = ?", (wager_id,)
        ).fetchone()
        return self._wager(row)

    def wagers_for(self, user_id: str, *, match_id: str | None = None) -> list[WagerRecord]:
        if match_id is None:
            rows = self._conn.execute(
                "SELECT * FROM wagers WHERE user_id = ? ORDER BY placed_at", (user_id,)
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM wagers WHERE user_id = ? AND match_id = ? ORDER BY placed_at",
                (user_id, match_id),
            ).fetchall()
        return [record for row in rows if (record := self._wager(row)) is not None]

    def set_closing_odds(self, wager_id: str, closing_odds: Money) -> None:
        self._conn.execute(
            "UPDATE wagers SET closing_odds = ? WHERE wager_id = ?",
            (str(closing_odds), wager_id),
        )
        self._conn.commit()

    @staticmethod
    def _wager(row: sqlite3.Row | None) -> WagerRecord | None:
        if row is None:
            return None
        closing = row["closing_odds"]
        placed = _parse_dt(row["placed_at"])
        assert placed is not None
        return WagerRecord(
            wager_id=row["wager_id"],
            user_id=row["user_id"],
            match_id=row["match_id"],
            match_title=row["match_title"],
            market_type=row["market_type"],
            selection=row["selection"],
            odds=Decimal(row["odds"]),
            closing_odds=Decimal(closing) if closing is not None else None,
            placed_at=placed,
        )

    # --- politika durumu -----------------------------------------------------
    def energy(self, user_id: str) -> tuple[int, datetime] | None:
        """Kayıtlı enerji durumu; henüz yoksa `None` (çağıran varsayılanı uygular)."""
        row = self._conn.execute(
            "SELECT energy, last_update FROM energy_state WHERE user_id = ?", (user_id,)
        ).fetchone()
        if row is None:
            return None
        last = _parse_dt(row["last_update"])
        assert last is not None
        return int(row["energy"]), last

    def save_energy(self, user_id: str, energy: int, last_update: datetime) -> None:
        self._conn.execute(
            "INSERT INTO energy_state (user_id, energy, last_update) VALUES (?, ?, ?)"
            " ON CONFLICT(user_id) DO UPDATE SET energy = excluded.energy,"
            " last_update = excluded.last_update",
            (user_id, energy, _iso(last_update)),
        )
        self._conn.commit()

    def cooldown(self, user_id: str) -> CooldownState:
        row = self._conn.execute(
            "SELECT tier, solvent_streak, locked_until FROM cooldown_state WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if row is None:
            return CooldownState()
        return CooldownState(
            tier=int(row["tier"]),
            solvent_streak=int(row["solvent_streak"]),
            locked_until=_parse_dt(row["locked_until"]),
        )

    def save_cooldown(self, user_id: str, state: CooldownState) -> None:
        locked = _iso(state.locked_until) if state.locked_until is not None else None
        self._conn.execute(
            "INSERT INTO cooldown_state (user_id, tier, solvent_streak, locked_until)"
            " VALUES (?, ?, ?, ?) ON CONFLICT(user_id) DO UPDATE SET tier = excluded.tier,"
            " solvent_streak = excluded.solvent_streak, locked_until = excluded.locked_until",
            (user_id, state.tier, state.solvent_streak, locked),
        )
        self._conn.commit()

    # --- maç kayıtları -------------------------------------------------------
    def save_match(self, record: MatchRecord) -> None:
        self._conn.execute(
            "INSERT OR IGNORE INTO matches (match_id, home_team, away_team, home_score,"
            " away_score, odds_1x2, seed, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                record.match_id,
                record.home_team,
                record.away_team,
                record.home_score,
                record.away_score,
                json.dumps({key: str(value) for key, value in record.odds_1x2.items()}),
                record.seed,
                _iso(self._clock()),
            ),
        )
        self._conn.commit()

    def matches(self) -> list[MatchRecord]:
        rows = self._conn.execute("SELECT * FROM matches ORDER BY created_at, match_id").fetchall()
        return [self._match(row) for row in rows]

    def match(self, match_id: str) -> MatchRecord | None:
        row = self._conn.execute("SELECT * FROM matches WHERE match_id = ?", (match_id,)).fetchone()
        return self._match(row) if row is not None else None

    @staticmethod
    def _match(row: sqlite3.Row) -> MatchRecord:
        raw = json.loads(row["odds_1x2"])
        return MatchRecord(
            match_id=row["match_id"],
            home_team=row["home_team"],
            away_team=row["away_team"],
            home_score=int(row["home_score"]),
            away_score=int(row["away_score"]),
            odds_1x2={key: Decimal(value) for key, value in raw.items()},
            seed=row["seed"],
        )

    # --- idempotency ---------------------------------------------------------
    def idempotent_response(self, user_id: str, key: str) -> str | None:
        row = self._conn.execute(
            "SELECT response FROM idempotency WHERE user_id = ? AND key = ?", (user_id, key)
        ).fetchone()
        return None if row is None else str(row["response"])

    def save_idempotent_response(self, user_id: str, key: str, response: str) -> None:
        self._conn.execute(
            "INSERT OR IGNORE INTO idempotency (user_id, key, response, created_at)"
            " VALUES (?, ?, ?, ?)",
            (user_id, key, response, _iso(self._clock())),
        )
        self._conn.commit()
