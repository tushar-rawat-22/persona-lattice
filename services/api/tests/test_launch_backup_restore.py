# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import shutil

from app.cases import CASE_STORE
from app.research import QuickResearchReport, ResearchKind


def test_stopped_sqlite_backup_restores_retained_case(monkeypatch, tmp_path) -> None:
    live_path = tmp_path / "live.db"
    backup_path = tmp_path / "live.db.pre-launch"
    restored_path = tmp_path / "restored.db"
    monkeypatch.setenv("PERSONALATTICE_DB_PATH", str(live_path))
    monkeypatch.setenv("PERSONALATTICE_CASE_RETENTION_DAYS", "30")

    report = QuickResearchReport(
        kind=ResearchKind.USERNAME,
        normalized_value="backup_smoke_user",
        observations=(),
        warnings=("synthetic launch backup fixture",),
        source_runs=(),
    )
    stored = CASE_STORE.create(
        seed_kind=report.kind,
        seed_value=report.normalized_value,
        report=report,
    )

    assert live_path.exists()
    shutil.copy2(live_path, backup_path)
    shutil.copy2(backup_path, restored_path)

    monkeypatch.setenv("PERSONALATTICE_DB_PATH", str(restored_path))
    restored = CASE_STORE.get(stored.id)

    assert restored is not None
    assert restored.id == stored.id
    assert restored.seed_kind is ResearchKind.USERNAME
    assert restored.seed_value == "backup_smoke_user"
    assert restored.report["kind"] == ResearchKind.USERNAME.value
