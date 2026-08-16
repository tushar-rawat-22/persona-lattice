# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from fastapi.testclient import TestClient

from app.admin_auth import LOGIN_THROTTLE, SESSION_STORE, hash_admin_password
from app.main import app


client = TestClient(app)
PASSWORD = "synthetic-admin-password-123!"


def _configure(monkeypatch, tmp_path) -> str:
    client.cookies.clear()
    SESSION_STORE.clear()
    LOGIN_THROTTLE.clear()
    monkeypatch.setenv("PERSONALATTICE_ADMIN_USERNAME", "admin")
    monkeypatch.setenv("PERSONALATTICE_ADMIN_PASSWORD_HASH", hash_admin_password(PASSWORD))
    monkeypatch.setenv("PERSONALATTICE_COOKIE_SECURE", "false")
    monkeypatch.setenv("PERSONALATTICE_SESSION_COOKIE", "personalattice_test_session")
    monkeypatch.setenv("PERSONALATTICE_DB_PATH", str(tmp_path / "cases.sqlite3"))
    login = client.post(
        "/v1/auth/login",
        json={"username": "admin", "password": PASSWORD},
    )
    assert login.status_code == 200, login.text
    return login.json()["csrf_token"]


def test_converged_case_requires_authentication(monkeypatch, tmp_path) -> None:
    _configure(monkeypatch, tmp_path)
    client.cookies.clear()
    response = client.post(
        "/v1/cases/run-converged",
        json={
            "kind": "phone",
            "value": "+919876543210",
            "purpose": "public_source_research",
            "consent_acknowledged": False,
        },
    )
    assert response.status_code == 401


def test_phone_converged_case_is_bounded_and_persisted(monkeypatch, tmp_path) -> None:
    csrf = _configure(monkeypatch, tmp_path)
    response = client.post(
        "/v1/cases/run-converged",
        headers={"X-PersonaLattice-CSRF": csrf},
        json={
            "kind": "phone",
            "value": "+919876543210",
            "purpose": "public_source_research",
            "consent_acknowledged": False,
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    report = body["report"]["converged_report"]

    assert report["executive_summary"]["research_node_count"] == 1
    assert report["executive_summary"]["pivot_edge_count"] == 0
    assert report["executive_summary"]["identity_claim"] is False
    assert report["safety_boundary"]["covert_ip_discovery"] is False
    assert report["nodes"][0]["observations"][0]["source"] == "libphonenumber_metadata"
    assert report["m5"]["is_identity_claim"] is False

    loaded = client.get(f"/v1/cases/{body['id']}")
    assert loaded.status_code == 200
    assert loaded.json()["report"]["converged_report"]["report_version"] == (
        "private-converged-evidence-report-v1"
    )
