# SPDX-License-Identifier: Apache-2.0
from fastapi.testclient import TestClient

from app.admin_auth import LOGIN_THROTTLE, SESSION_STORE, hash_admin_password
from app.main import app


client = TestClient(app)
PASSWORD = "synthetic-admin-password-123!"


def _configure_admin(monkeypatch) -> None:
    client.cookies.clear()
    SESSION_STORE.clear()
    LOGIN_THROTTLE.clear()
    monkeypatch.setenv("PERSONALATTICE_ADMIN_USERNAME", "admin")
    monkeypatch.setenv("PERSONALATTICE_ADMIN_PASSWORD_HASH", hash_admin_password(PASSWORD))
    monkeypatch.setenv("PERSONALATTICE_COOKIE_SECURE", "false")
    monkeypatch.setenv("PERSONALATTICE_SESSION_COOKIE", "personalattice_test_session")


def test_authenticated_private_responses_are_not_cacheable(monkeypatch) -> None:
    _configure_admin(monkeypatch)
    login = client.post(
        "/v1/auth/login",
        json={"username": "admin", "password": PASSWORD},
    )
    assert login.status_code == 200, login.text
    assert login.headers["Cache-Control"] == "no-store"

    session = client.get("/v1/auth/session")
    assert session.status_code == 200, session.text
    assert session.headers["Cache-Control"] == "no-store"

    cases = client.get("/v1/cases")
    assert cases.status_code == 200, cases.text
    assert cases.headers["Cache-Control"] == "no-store"


def test_denied_private_response_is_not_cacheable(monkeypatch) -> None:
    _configure_admin(monkeypatch)
    denied = client.post(
        "/v1/auth/login",
        json={"username": "admin", "password": "wrong-password-value"},
    )
    assert denied.status_code == 401, denied.text
    assert denied.headers["Cache-Control"] == "no-store"
