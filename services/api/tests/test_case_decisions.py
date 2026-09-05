# SPDX-License-Identifier: Apache-2.0
from fastapi.testclient import TestClient

from app.admin_auth import LOGIN_THROTTLE, SESSION_STORE, hash_admin_password
from app.cases import CASE_STORE
from app.main import app
from app.research import QuickObservation, QuickResearchReport, ResearchKind


client = TestClient(app)
PASSWORD = "synthetic-admin-password-123!"


def _configure(monkeypatch, tmp_path) -> None:
    client.cookies.clear()
    SESSION_STORE.clear()
    LOGIN_THROTTLE.clear()
    monkeypatch.setenv("PERSONALATTICE_ADMIN_USERNAME", "admin")
    monkeypatch.setenv("PERSONALATTICE_ADMIN_PASSWORD_HASH", hash_admin_password(PASSWORD))
    monkeypatch.setenv("PERSONALATTICE_COOKIE_SECURE", "false")
    monkeypatch.setenv("PERSONALATTICE_SESSION_COOKIE", "personalattice_test_session")
    monkeypatch.setenv("PERSONALATTICE_DB_PATH", str(tmp_path / "cases.sqlite3"))
    monkeypatch.setenv("PERSONALATTICE_CASE_RETENTION_DAYS", "30")


def _login() -> str:
    response = client.post(
        "/v1/auth/login",
        json={"username": "admin", "password": PASSWORD},
    )
    assert response.status_code == 200, response.text
    return response.json()["csrf_token"]


def _case_id() -> str:
    report = QuickResearchReport(
        kind=ResearchKind.EMAIL,
        normalized_value="synthetic@example.test",
        observations=(
            QuickObservation(
                source="synthetic",
                source_locator="local://synthetic",
                summary="Synthetic retained evidence.",
                details={"identity_claim": False},
            ),
        ),
    )
    record = CASE_STORE.create(
        seed_kind=ResearchKind.EMAIL,
        seed_value="synthetic@example.test",
        report=report,
    )
    return str(record.id)


def test_case_decisions_are_private_append_only_and_survive_reopen(monkeypatch, tmp_path) -> None:
    _configure(monkeypatch, tmp_path)
    case_id = _case_id()

    assert client.get(f"/v1/cases/{case_id}/decisions").status_code == 401
    assert client.post(
        f"/v1/cases/{case_id}/decisions",
        json={"disposition": "await_more_evidence", "rationale": "Need a second source."},
    ).status_code == 401

    csrf = _login()
    assert client.post(
        f"/v1/cases/{case_id}/decisions",
        json={"disposition": "await_more_evidence", "rationale": "Need a second source."},
    ).status_code == 403

    created = client.post(
        f"/v1/cases/{case_id}/decisions",
        headers={"X-PersonaLattice-CSRF": csrf},
        json={
            "disposition": "await_more_evidence",
            "rationale": "  Need a second independent source before handoff.  ",
        },
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["case_id"] == case_id
    assert body["disposition"] == "await_more_evidence"
    assert body["rationale"] == "Need a second independent source before handoff."
    assert body["created_at"]

    reopened = client.get(f"/v1/cases/{case_id}/decisions")
    assert reopened.status_code == 200, reopened.text
    assert reopened.json() == [body]

    second = client.post(
        f"/v1/cases/{case_id}/decisions",
        headers={"X-PersonaLattice-CSRF": csrf},
        json={"disposition": "ready_for_handoff", "rationale": "Corroboration reviewed."},
    )
    assert second.status_code == 201, second.text
    listed = client.get(f"/v1/cases/{case_id}/decisions")
    assert [item["disposition"] for item in listed.json()] == [
        "ready_for_handoff",
        "await_more_evidence",
    ]


def test_case_decision_validation_and_case_deletion_boundary(monkeypatch, tmp_path) -> None:
    _configure(monkeypatch, tmp_path)
    case_id = _case_id()
    csrf = _login()
    headers = {"X-PersonaLattice-CSRF": csrf}

    blank = client.post(
        f"/v1/cases/{case_id}/decisions",
        headers=headers,
        json={"disposition": "continue_research", "rationale": "   "},
    )
    assert blank.status_code == 422

    invalid = client.post(
        f"/v1/cases/{case_id}/decisions",
        headers=headers,
        json={"disposition": "identity_confirmed", "rationale": "Not an allowed state."},
    )
    assert invalid.status_code == 422

    created = client.post(
        f"/v1/cases/{case_id}/decisions",
        headers=headers,
        json={"disposition": "close_case", "rationale": "No further action is justified."},
    )
    assert created.status_code == 201

    deleted = client.delete(f"/v1/cases/{case_id}", headers=headers)
    assert deleted.status_code == 204
    assert client.get(f"/v1/cases/{case_id}/decisions").status_code == 404
