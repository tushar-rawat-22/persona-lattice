# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import os
from pathlib import Path
import sqlite3
import stat

import pytest

from app.sqlite_storage import private_runtime_database_path


pytestmark = pytest.mark.skipif(
    os.name != "posix",
    reason="Owner-only SQLite mode is a POSIX launch-host contract.",
)


def _mode(path: Path) -> int:
    return stat.S_IMODE(path.stat().st_mode)


def test_new_runtime_database_ignores_permissive_umask(monkeypatch, tmp_path: Path) -> None:
    database = tmp_path / "runtime.db"
    monkeypatch.setenv("PERSONALATTICE_DB_PATH", str(database))

    previous_umask = os.umask(0)
    try:
        resolved = private_runtime_database_path()
    finally:
        os.umask(previous_umask)

    assert resolved == database
    assert database.is_file()
    assert _mode(database) == 0o600


def test_existing_runtime_database_is_tightened_to_owner_only(monkeypatch, tmp_path: Path) -> None:
    database = tmp_path / "runtime.db"
    database.write_bytes(b"")
    database.chmod(0o644)
    monkeypatch.setenv("PERSONALATTICE_DB_PATH", str(database))

    private_runtime_database_path()

    assert _mode(database) == 0o600


@pytest.mark.parametrize("target_exists", [True, False])
def test_runtime_database_refuses_leaf_symlink_without_touching_target(
    monkeypatch,
    tmp_path: Path,
    target_exists: bool,
) -> None:
    target = tmp_path / "target.db"
    if target_exists:
        target.write_bytes(b"")
        target.chmod(0o644)
    database = tmp_path / "runtime.db"
    database.symlink_to(target)
    monkeypatch.setenv("PERSONALATTICE_DB_PATH", str(database))

    with pytest.raises(RuntimeError, match="symbolic link"):
        private_runtime_database_path()

    if target_exists:
        assert _mode(target) == 0o644
    else:
        assert not target.exists()


def test_wal_sidecars_remain_owner_only_under_permissive_umask(
    monkeypatch,
    tmp_path: Path,
) -> None:
    database = tmp_path / "runtime.db"
    monkeypatch.setenv("PERSONALATTICE_DB_PATH", str(database))

    previous_umask = os.umask(0)
    writer: sqlite3.Connection | None = None
    reader: sqlite3.Connection | None = None
    try:
        writer = sqlite3.connect(private_runtime_database_path())
        journal_mode = writer.execute("PRAGMA journal_mode = WAL").fetchone()
        assert journal_mode is not None and journal_mode[0].lower() == "wal"
        writer.execute("CREATE TABLE privacy_probe (value TEXT NOT NULL)")
        writer.execute("INSERT INTO privacy_probe (value) VALUES ('retained')")
        writer.commit()

        reader = sqlite3.connect(database)
        assert reader.execute("SELECT value FROM privacy_probe").fetchone() == ("retained",)

        wal_path = Path(f"{database}-wal")
        shm_path = Path(f"{database}-shm")
        assert wal_path.is_file()
        assert shm_path.is_file()
        assert _mode(database) == 0o600
        assert _mode(wal_path) == 0o600
        assert _mode(shm_path) == 0o600
    finally:
        if reader is not None:
            reader.close()
        if writer is not None:
            writer.close()
        os.umask(previous_umask)
