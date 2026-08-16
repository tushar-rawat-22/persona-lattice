# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from uuid import uuid4

import pytest

from app.audit import AuditStore


def test_audit_store_records_only_supplied_bounded_metadata(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("PERSONALATTICE_DB_PATH", str(tmp_path / "audit.db"))
    store = AuditStore()
    case_id = uuid4()

    event = store.record(
        "case.read",
        case_id=case_id,
        details={"result": "allowed"},
    )
    events = store.list_recent()

    assert event.case_id == case_id
    assert events[0].event_type == "case.read"
    assert events[0].details == {"result": "allowed"}


def test_audit_store_rejects_oversized_details(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("PERSONALATTICE_DB_PATH", str(tmp_path / "audit.db"))
    store = AuditStore()

    with pytest.raises(ValueError, match="configured limit"):
        store.record("case.read", details={"blob": "x" * 5000})


def test_audit_store_bounds_listing(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("PERSONALATTICE_DB_PATH", str(tmp_path / "audit.db"))
    store = AuditStore()

    with pytest.raises(ValueError, match="between 1 and 500"):
        store.list_recent(limit=0)
