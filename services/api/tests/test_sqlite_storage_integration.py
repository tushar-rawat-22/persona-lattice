# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import os
from pathlib import Path
import stat

import pytest

from app.audit import AUDIT_STORE
from app.cases import CASE_STORE
from app.research import QuickResearchReport, ResearchKind


pytestmark = pytest.mark.skipif(
    os.name != "posix",
    reason="Owner-only SQLite mode is a POSIX launch-host contract.",
)


def _mode(path: Path) -> int:
    return stat.S_IMODE(path.stat().st_mode)


def test_case_and_audit_stores_share_private_runtime_database(monkeypatch, tmp_path: Path) -> None:
    database = tmp_path / "runtime.db"
    monkeypatch.setenv("PERSONALATTICE_DB_PATH", str(database))
    monkeypatch.setenv("PERSONALATTICE_CASE_RETENTION_DAYS", "30")

    previous_umask = os.umask(0)
    try:
        stored = CASE_STORE.create(
            seed_kind=ResearchKind.USERNAME,
            seed_value="privacy_probe",
            report=QuickResearchReport(
                kind=ResearchKind.USERNAME,
                normalized_value="privacy_probe",
                observations=(),
                warnings=(),
                source_runs=(),
            ),
        )
        AUDIT_STORE.record("case.read", case_id=stored.id)
    finally:
        os.umask(previous_umask)

    assert CASE_STORE.get(stored.id) is not None
    assert any(event.case_id == stored.id for event in AUDIT_STORE.list_recent(limit=10))
    assert _mode(database) == 0o600
