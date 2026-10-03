"""S5 — veri dayanıklılığı: yedeğin gerçekten kurtarılabilir olduğunu **kanıtlar**.

Neden bu test: "yedek var" ile "kayıt kurtarılabilir" aynı şey değil. WAL modunda canlı
veritabanını düz kopyalamak yedeği yırtar; `integrity_check` geçen **bayat** bir kopya da
sağlam görünür. Kanıt, **bilinen bir commit'li satırın geri gelen kopyada bulunmasıdır**.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from decimal import Decimal as D
from pathlib import Path

import pytest

from fairplay_simulator.core.ledger import EntryType, Ledger, LedgerEntry
from fairplay_simulator.core.nav import Fund
from fairplay_simulator.repo import Repository

MOMENT = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


def _seed(repo: Repository, username: str) -> str:
    """Tipik bir defter yazar ve kullanıcı kimliğini döner."""
    user = repo.create_user(username, f"{username}@example.com", "hash")
    ledger = Ledger()
    ledger.deposit(D("1000"))
    ledger.place_wager("w1", D("100"))
    ledger.settle_wager("w1", D("100"), D("250"))
    ledger.refill(D("1000"))
    repo.append_entries(user.id, ledger.entries)
    return user.id


def test_restore_drill_recovers_the_committed_ledger(tmp_path: Path) -> None:
    """Yedek al → **yeni dosyaya** geri yükle → defter ve fon durumu birebir döner."""
    backup = tmp_path / "backup.db"
    with Repository(tmp_path / "live.db", clock=lambda: MOMENT) as repo:
        user_id = _seed(repo, "aytek")
        entries_at_backup = repo.entries(user_id)
        fund_at_backup = Fund.replay(entries_at_backup)

        repo.backup_to(backup)

        # Yedekten SONRA yazılan kayıt yedeğe girmemeli: yedek anlık görüntüdür.
        repo.append_entry(
            user_id,
            LedgerEntry(seq=0, entry_type=EntryType.REFILL, amount=D("500")),
        )
        assert len(repo.entries(user_id)) == len(entries_at_backup) + 1

    assert backup.exists(), "yedek dosyası oluşmadı"

    with Repository(backup) as restored:
        entries_restored = restored.entries(user_id)
        assert entries_restored == entries_at_backup, "geri yüklenen defter birebir aynı olmalı"
        fund_restored = Fund.replay(entries_restored)
        assert fund_restored.nav == fund_at_backup.nav
        assert fund_restored.units == fund_at_backup.units
        assert fund_restored.twr == fund_at_backup.twr


def test_backup_passes_integrity_check_and_carries_no_wal_sidecar(tmp_path: Path) -> None:
    """Yedek bütünlükten geçer; online API WAL yan dosyasını taşımaz (düz kopyadan farkı)."""
    backup = tmp_path / "backup.db"
    with Repository(tmp_path / "live.db", clock=lambda: MOMENT) as repo:
        _seed(repo, "aytek")
        repo.backup_to(backup)

    connection = sqlite3.connect(str(backup))
    try:
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        # `_seed` dört kayıt yazar: deposit + place_wager + settle_wager + refill.
        assert connection.execute("SELECT COUNT(*) FROM ledger_entries").fetchone()[0] == 4
    finally:
        connection.close()

    assert not Path(str(backup) + "-wal").exists()
    assert backup.stat().st_size > 0


def test_durability_decisions_are_explicit(tmp_path: Path) -> None:
    """Kararlar varsayılana bırakılmadı: WAL açık, `synchronous=NORMAL`, FK zorlaması açık."""
    with Repository(tmp_path / "pragmas.db") as repo:
        assert repo.journal_mode() == "wal"
        assert repo.synchronous() == 1  # 1 = NORMAL
        assert repo.foreign_keys_enabled() is True


def test_foreign_keys_are_actually_enforced(tmp_path: Path) -> None:
    """FK pragması kozmetik değil: olmayan kullanıcıya defter kaydı yazılamaz."""
    with Repository(tmp_path / "fk.db", clock=lambda: MOMENT) as repo:
        orphan = LedgerEntry(seq=0, entry_type=EntryType.DEPOSIT, amount=D("1000"))
        with pytest.raises(sqlite3.IntegrityError):
            repo.append_entry("olmayan-kullanici", orphan)
