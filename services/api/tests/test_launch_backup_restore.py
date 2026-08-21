# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import shutil

import pytest

from app.cases import CASE_STORE
from app.database_backup import DatabaseBackupError, backup_sqlite_database
from app.research import QuickResearchReport, ResearchKind


def _create_retained_case(monkeypatch, live_path):
    monkeypatch.setenv("PERSONALATTICE_DB_PATH", str(live_path))
    monkeypatch.setenv("PERSONALATTICE_CASE_RETENTION_DAYS", "30")
    report = QuickResearchReport(
        kind=ResearchKind.USERNAME,
        normalized_value="backup_smoke_user",
        observations=(),
        warnings=("synthetic launch backup fixture",),
        source_runs=(),
    )
    return CASE_STORE.create(
        seed_kind=report.kind,
        seed_value=report.normalized_value,
        report=report,
    )


def test_sqlite_backup_restores_retained_case_with_wal_enabled(monkeypatch, tmp_path) -> None:
    live_path = tmp_path / "live.db"
    backup_path = tmp_path / "live.db.pre-launch"
    restored_path = tmp_path / "restored.db"
    stored = _create_retained_case(monkeypatch, live_path)

    assert live_path.exists()
    backup_sqlite_database(live_path, backup_path)
    shutil.copy2(backup_path, restored_path)

    monkeypatch.setenv("PERSONALATTICE_DB_PATH", str(restored_path))
    restored = CASE_STORE.get(stored.id)

    assert restored is not None
    assert restored.id == stored.id
    assert restored.seed_kind is ResearchKind.USERNAME
    assert restored.seed_value == "backup_smoke_user"
    assert restored.report["kind"] == ResearchKind.USERNAME.value


def test_launch_backup_refuses_to_overwrite_existing_snapshot(monkeypatch, tmp_path) -> None:
    live_path = tmp_path / "live.db"
    backup_path = tmp_path / "live.db.pre-launch"
    _create_retained_case(monkeypatch, live_path)
    backup_sqlite_database(live_path, backup_path)

    with pytest.raises(DatabaseBackupError, match="refusing to overwrite"):
        backup_sqlite_database(live_path, backup_path)
