# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from fastapi.testclient import TestClient

from app.admin_auth import LOGIN_THROTTLE, SESSION_STORE, hash_admin_password
from app.main import app
from app.research import QuickResearchReport, ResearchKind


PASSWORD = "launch-smoke-admin-password-123!"


def _configure(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("PERSONALATTICE_ADMIN_USERNAME", "launch-admin")
    monkeypatch.setenv("PERSONALATTICE_ADMIN_PASSWORD_HASH", hash_admin_password(PASSWORD))
    monkeypatch.setenv("PERSONALATTICE_COOKIE_SECURE", "false")
    monkeypatch.setenv("PERSONALATTICE_SESSION_COOKIE", "launch_smoke_session")
    monkeypatch.setenv("PERSONALATTICE_DB_PATH", str(tmp_path / "launch-smoke.db"))
    monkeypatch.setenv("PERSONALATTICE_CASE_RETENTION_DAYS", "30")
    SESSION_STORE.clear()
    LOGIN_THROTTLE.clear()


def test_one_admin_case_lifecycle_smoke(monkeypatch, tmp_path) -> None:
    _configure(monkeypatch, tmp_path)
    client = TestClient(app)

    async def fake_research(payload):
        return QuickResearchReport(
            kind=payload.kind,
            normalized_value=payload.value,
            observations=(),
            warnings=("launch smoke uses a synthetic provider-free report",),
            source_runs=(),
        )

    monkeypatch.setattr("app.main._execute_research", fake_research)

    assert client.get("/health").status_code == 200
    assert client.get("/v1/cases").status_code == 401

    wrong = client.post(
        "/v1/auth/login",
        json={"username": "launch-admin", "password": "wrong-password"},
    )
    assert wrong.status_code == 401
    assert not client.cookies

    login = client.post(
        "/v1/auth/login",
        json={"username": "launch-admin", "password": PASSWORD},
    )
    assert login.status_code == 200
    csrf = login.json()["csrf_token"]
    assert client.get("/v1/auth/session").status_code == 200

    payload = {
        "kind": ResearchKind.USERNAME.value,
        "value": "launch_smoke_user",
        "purpose": "self_audit",
        "consent_acknowledged": True,
    }
    assert client.post("/v1/cases/run", json=payload).status_code == 403

    headers = {"X-PersonaLattice-CSRF": csrf}
    created = client.post("/v1/cases/run", json=payload, headers=headers)
    assert created.status_code == 200, created.text
    case_id = created.json()["id"]

    listed = client.get("/v1/cases?limit=8")
    assert listed.status_code == 200
    summaries = listed.json()
    assert [item["id"] for item in summaries] == [case_id]
    assert "report" not in summaries[0]

    opened = client.get(f"/v1/cases/{case_id}")
    assert opened.status_code == 200
    assert opened.json()["report"]["kind"] == ResearchKind.USERNAME.value

    deleted = client.delete(f"/v1/cases/{case_id}", headers=headers)
    assert deleted.status_code == 204
    assert client.get(f"/v1/cases/{case_id}").status_code == 404
    assert client.get("/v1/cases?limit=8").json() == []

    logout = client.post("/v1/auth/logout", headers=headers)
    assert logout.status_code == 204
    assert client.get("/v1/auth/session").status_code == 401
