# SPDX-License-Identifier: Apache-2.0
from fastapi.testclient import TestClient

from app.admin_auth import LOGIN_THROTTLE, SESSION_STORE, hash_admin_password
from app.main import app


client = TestClient(app)
PASSWORD = "synthetic-admin-password-123!"


def _login(monkeypatch) -> str:
    client.cookies.clear()
    SESSION_STORE.clear()
    LOGIN_THROTTLE.clear()
    monkeypatch.setenv("PERSONALATTICE_ADMIN_USERNAME", "admin")
    monkeypatch.setenv("PERSONALATTICE_ADMIN_PASSWORD_HASH", hash_admin_password(PASSWORD))
    monkeypatch.setenv("PERSONALATTICE_COOKIE_SECURE", "false")
    monkeypatch.setenv("PERSONALATTICE_SESSION_COOKIE", "personalattice_test_session")

    response = client.post(
        "/v1/auth/login",
        json={"username": "admin", "password": PASSWORD},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["authenticated"] is True
    return body["csrf_token"]


def _csrf(token: str) -> dict[str, str]:
    return {"X-PersonaLattice-CSRF": token}


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_anonymous_intake_is_denied(monkeypatch) -> None:
    client.cookies.clear()
    SESSION_STORE.clear()
    monkeypatch.setenv("PERSONALATTICE_ADMIN_USERNAME", "admin")
    monkeypatch.setenv("PERSONALATTICE_ADMIN_PASSWORD_HASH", hash_admin_password(PASSWORD))
    monkeypatch.setenv("PERSONALATTICE_COOKIE_SECURE", "false")
    monkeypatch.setenv("PERSONALATTICE_SESSION_COOKIE", "personalattice_test_session")

    response = client.post(
        "/v1/intake/preview",
        json={"purpose": "self_audit", "consent_acknowledged": True},
    )

    assert response.status_code == 401
    assert "admin authentication" in response.json()["detail"].lower()


def test_authenticated_write_without_csrf_is_denied(monkeypatch) -> None:
    _login(monkeypatch)
    response = client.post(
        "/v1/intake/preview",
        json={"purpose": "self_audit", "consent_acknowledged": True},
    )
    assert response.status_code == 403
    assert "csrf" in response.json()["detail"].lower()


def test_wrong_admin_password_is_denied(monkeypatch) -> None:
    client.cookies.clear()
    SESSION_STORE.clear()
    LOGIN_THROTTLE.clear()
    monkeypatch.setenv("PERSONALATTICE_ADMIN_USERNAME", "admin")
    monkeypatch.setenv("PERSONALATTICE_ADMIN_PASSWORD_HASH", hash_admin_password(PASSWORD))
    monkeypatch.setenv("PERSONALATTICE_COOKIE_SECURE", "false")
    monkeypatch.setenv("PERSONALATTICE_SESSION_COOKIE", "personalattice_test_session")

    response = client.post(
        "/v1/auth/login",
        json={"username": "admin", "password": "wrong-password-value"},
    )

    assert response.status_code == 401
    assert not client.cookies


def test_preview_normalizes_intake(monkeypatch) -> None:
    csrf = _login(monkeypatch)
    response = client.post(
        "/v1/intake/preview",
        headers=_csrf(csrf),
        json={
            "purpose": "self_audit",
            "consent_acknowledged": True,
            "phones": ["+91 98765 43210"],
            "emails": [" Test@Example.com "],
            "usernames": ["@demo_user"],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "planned_only"
    assert body["normalized"]["phones"] == ["+919876543210"]
    assert body["normalized"]["emails"] == ["Test@example.com"]
    assert body["normalized"]["usernames"] == ["demo_user"]


def test_preview_deduplicates_and_warns_on_malformed_identifiers(monkeypatch) -> None:
    csrf = _login(monkeypatch)
    response = client.post(
        "/v1/intake/preview",
        headers=_csrf(csrf),
        json={
            "purpose": "self_audit",
            "consent_acknowledged": True,
            "phones": ["+91 98765 43210", "+919876543210", "not-a-phone"],
            "emails": ["TEST@Example.com", "TEST@example.com", "broken email"],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["normalized"]["phones"] == ["+919876543210"]
    assert body["normalized"]["emails"] == ["TEST@example.com"]
    assert len(body["warnings"]) == 2


def test_regulated_decision_is_blocked(monkeypatch) -> None:
    csrf = _login(monkeypatch)
    response = client.post(
        "/v1/intake/preview",
        headers=_csrf(csrf),
        json={
            "purpose": "employment_decision",
            "consent_acknowledged": True,
            "full_name": "Synthetic Person",
        },
    )
    assert response.status_code == 422


def test_consent_is_required_for_self_audit(monkeypatch) -> None:
    csrf = _login(monkeypatch)
    response = client.post(
        "/v1/intake/preview",
        headers=_csrf(csrf),
        json={
            "purpose": "self_audit",
            "consent_acknowledged": False,
            "full_name": "Synthetic Person",
        },
    )
    assert response.status_code == 422


def test_logout_revokes_current_admin_session(monkeypatch) -> None:
    csrf = _login(monkeypatch)
    assert client.get("/v1/auth/session").status_code == 200

    logout = client.post("/v1/auth/logout", headers=_csrf(csrf))
    assert logout.status_code == 204
    assert client.get("/v1/auth/session").status_code == 401
