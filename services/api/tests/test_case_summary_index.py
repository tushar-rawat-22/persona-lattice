# SPDX-License-Identifier: Apache-2.0
from datetime import UTC, datetime, timedelta
from pathlib import Path
import sqlite3

from fastapi.testclient import TestClient

from app.admin_auth import LOGIN_THROTTLE, SESSION_STORE, hash_admin_password
from app.cases import CASE_STORE
from app.main import app
from app.research import ResearchKind


client = TestClient(app)
PASSWORD = "synthetic-admin-password-123!"
ROOT = Path(__file__).resolve().parents[3]
CASE_UI = ROOT / "apps/web/app/admin/quick-research.tsx"
CASE_NAVIGATION_UI = ROOT / "apps/web/app/admin/case-navigation.tsx"


def _configure(monkeypatch, tmp_path) -> Path:
    client.cookies.clear()
    SESSION_STORE.clear()
    LOGIN_THROTTLE.clear()
    database_path = tmp_path / "cases.sqlite3"
    monkeypatch.setenv("PERSONALATTICE_ADMIN_USERNAME", "admin")
    monkeypatch.setenv("PERSONALATTICE_ADMIN_PASSWORD_HASH", hash_admin_password(PASSWORD))
    monkeypatch.setenv("PERSONALATTICE_COOKIE_SECURE", "false")
    monkeypatch.setenv("PERSONALATTICE_SESSION_COOKIE", "personalattice_test_session")
    monkeypatch.setenv("PERSONALATTICE_DB_PATH", str(database_path))
    monkeypatch.setenv("PERSONALATTICE_CASE_RETENTION_DAYS", "30")
    return database_path


def _login() -> None:
    response = client.post(
        "/v1/auth/login",
        json={"username": "admin", "password": PASSWORD},
    )
    assert response.status_code == 200, response.text


def test_summary_storage_never_needs_report_json(monkeypatch, tmp_path) -> None:
    database_path = _configure(monkeypatch, tmp_path)
    now = datetime(2026, 8, 20, 8, 0, tzinfo=UTC)
    created = CASE_STORE.create_payload(
        seed_kind=ResearchKind.EMAIL,
        seed_value="synthetic@example.test",
        report_payload={"evidence": "must-not-be-listed"},
        now=now,
    )

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            "UPDATE research_cases SET report_json = ? WHERE id = ?",
            ("{not-valid-json" + ("x" * 100_000), str(created.id)),
        )
        connection.commit()

    summaries, next_cursor = CASE_STORE.list_summaries(now=now + timedelta(hours=1))

    assert next_cursor is None
    assert len(summaries) == 1
    summary = summaries[0]
    assert summary.id == created.id
    assert summary.seed_value == "synthetic@example.test"
    assert not hasattr(summary, "report")


def test_summary_cursor_is_bounded_stable_and_non_overlapping(monkeypatch, tmp_path) -> None:
    _configure(monkeypatch, tmp_path)
    base = datetime(2026, 8, 20, 9, 0, tzinfo=UTC)
    created = [
        CASE_STORE.create_payload(
            seed_kind=ResearchKind.USERNAME,
            seed_value=f"seed-{index}",
            report_payload={"index": index},
            now=base + timedelta(minutes=index),
        )
        for index in range(3)
    ]

    first_page, cursor = CASE_STORE.list_summaries(limit=2, now=base + timedelta(hours=1))
    assert [record.id for record in first_page] == [created[2].id, created[1].id]
    assert cursor is not None

    second_page, second_cursor = CASE_STORE.list_summaries(
        limit=2,
        cursor=cursor,
        now=base + timedelta(hours=1),
    )
    assert [record.id for record in second_page] == [created[0].id]
    assert second_cursor is None
    assert {record.id for record in first_page}.isdisjoint(record.id for record in second_page)


def test_summary_cursor_and_limit_fail_closed(monkeypatch, tmp_path) -> None:
    _configure(monkeypatch, tmp_path)

    for limit in (0, 51):
        try:
            CASE_STORE.list_summaries(limit=limit)
        except ValueError as exc:
            assert "between 1 and 50" in str(exc)
        else:
            raise AssertionError("out-of-range summary limit was accepted")

    try:
        CASE_STORE.list_summaries(cursor="not-a-valid-cursor")
    except ValueError as exc:
        assert str(exc) == "Case list cursor is invalid."
    else:
        raise AssertionError("invalid summary cursor was accepted")


def test_case_list_api_returns_only_navigation_metadata(monkeypatch, tmp_path) -> None:
    _configure(monkeypatch, tmp_path)
    _login()
    now = datetime.now(UTC)
    created = [
        CASE_STORE.create_payload(
            seed_kind=ResearchKind.EMAIL,
            seed_value=f"case-{index}@example.test",
            report_payload={"secret_evidence": f"evidence-{index}"},
            now=now + timedelta(seconds=index),
        )
        for index in range(2)
    ]

    listed = client.get("/v1/cases?limit=1")
    assert listed.status_code == 200, listed.text
    assert listed.headers.get("X-PersonaLattice-Next-Cursor")
    body = listed.json()
    assert len(body) == 1
    assert set(body[0]) == {"id", "created_at", "expires_at", "seed_kind", "seed_value"}
    assert "report" not in body[0]
    assert "secret_evidence" not in listed.text

    loaded = client.get(f"/v1/cases/{created[1].id}")
    assert loaded.status_code == 200, loaded.text
    assert loaded.json()["report"]["secret_evidence"] == "evidence-1"


def test_private_web_uses_summary_list_then_full_case_fetch() -> None:
    source = CASE_UI.read_text(encoding="utf-8")
    navigation = CASE_NAVIGATION_UI.read_text(encoding="utf-8")

    assert 'request("/v1/cases?limit=8")' in source
    assert "request(`/v1/cases/${caseId}`)" in source
    assert 'import { CaseNavigation } from "./case-navigation";' in source
    assert "<CaseNavigation" in source
    assert "cases={recentCases}" in source
    assert "onOpenCase={openCase}" in source

    assert "cases.map" not in navigation
    assert "visibleCases.map" in navigation
    assert "item.report" not in navigation

    open_case_start = source.index("async function openCase")
    delete_case_start = source.index("async function deleteCase")
    open_case = source[open_case_start:delete_case_start]
    assert "const stored = (await response.json()) as StoredCase;" in open_case
    assert "setActiveCase(stored);" in open_case
    assert "isCurrentCaseContext(generation)" in open_case
