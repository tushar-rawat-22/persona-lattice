# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from uuid import uuid4

import pytest

from app.audit import AuditStore


def test_audit_store_records_only_approved_operational_metadata(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("PERSONALATTICE_DB_PATH", str(tmp_path / "audit.db"))
    store = AuditStore()
    case_id = uuid4()

    event = store.record(
        "case.list",
        case_id=case_id,
        details={"result_count": 2, "has_more": True},
    )
    events = store.list_recent()

    assert event.case_id == case_id
    assert events[0].event_type == "case.list"
    assert events[0].details == {"result_count": 2, "has_more": True}


@pytest.mark.parametrize(
    "details",
    [
        {"username": "alice"},
        {"email": "alice@example.test"},
        {"password": "secret"},
        {"source_locator": "https://example.test/profile"},
        {"provider_payload": {"token": "secret"}},
    ],
)
def test_audit_store_rejects_unapproved_sensitive_detail_keys(
    monkeypatch,
    tmp_path,
    details,
) -> None:
    monkeypatch.setenv("PERSONALATTICE_DB_PATH", str(tmp_path / "audit.db"))
    store = AuditStore()

    with pytest.raises(ValueError, match="unapproved key"):
        store.record("case.read", details=details)


def test_audit_store_rejects_unknown_event_even_without_details(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("PERSONALATTICE_DB_PATH", str(tmp_path / "audit.db"))
    store = AuditStore()

    with pytest.raises(ValueError, match="approved vocabulary"):
        store.record("case.future_event")


def test_audit_store_rejects_malformed_event_type(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("PERSONALATTICE_DB_PATH", str(tmp_path / "audit.db"))
    store = AuditStore()

    with pytest.raises(ValueError, match="invalid format"):
        store.record("case.read\nforged")


@pytest.mark.parametrize(
    ("event_type", "details"),
    [
        ("research.quick", {"kind": "name"}),
        ("case.create", {"mode": "recursive"}),
        ("file.review.confirm", {"candidate_type": "person"}),
        ("case.list", {"result_count": -1, "has_more": False}),
        ("case.delete", {"deleted": 1}),
    ],
)
def test_audit_store_rejects_out_of_contract_values(
    monkeypatch,
    tmp_path,
    event_type,
    details,
) -> None:
    monkeypatch.setenv("PERSONALATTICE_DB_PATH", str(tmp_path / "audit.db"))
    store = AuditStore()

    with pytest.raises(ValueError):
        store.record(event_type, details=details)


def test_audit_store_bounds_listing(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("PERSONALATTICE_DB_PATH", str(tmp_path / "audit.db"))
    store = AuditStore()

    with pytest.raises(ValueError, match="between 1 and 500"):
        store.list_recent(limit=0)
