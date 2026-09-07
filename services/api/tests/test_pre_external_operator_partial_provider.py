# SPDX-License-Identifier: Apache-2.0
from fastapi.testclient import TestClient

from app.admin_auth import LOGIN_THROTTLE, SESSION_STORE, hash_admin_password
from app.main import app
from app.providers.errors import ProviderRemoteRateLimitError


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
    monkeypatch.setenv("PERSONALATTICE_DB_PATH", str(tmp_path / "partial-provider.sqlite3"))
    monkeypatch.setenv("PERSONALATTICE_CASE_RETENTION_DAYS", "30")
    monkeypatch.setenv("BRAVE_SEARCH_API_KEY", "synthetic-test-only-key")


def _login() -> str:
    response = client.post(
        "/v1/auth/login",
        json={"username": "admin", "password": PASSWORD},
    )
    assert response.status_code == 200, response.text
    return response.json()["csrf_token"]


def test_partial_provider_failure_persists_useful_truthful_case(monkeypatch, tmp_path) -> None:
    """#340 gate: provider failure stays failure while useful independent evidence survives."""

    _configure(monkeypatch, tmp_path)

    async def remote_rate_limit(*args, **kwargs):
        raise ProviderRemoteRateLimitError("synthetic remote rate limit")

    monkeypatch.setattr("app.research.DEFAULT_PROVIDER_RUNTIME.execute", remote_rate_limit)
    csrf = _login()

    created = client.post(
        "/v1/cases/run",
        headers={"X-PersonaLattice-CSRF": csrf},
        json={
            "kind": "phone",
            "value": "+14155552671",
            "purpose": "public_source_research",
            "consent_acknowledged": False,
        },
    )

    assert created.status_code == 200, created.text
    body = created.json()
    report = body["report"]

    assert report["observations"] == [
        {
            "source": "libphonenumber_metadata",
            "source_locator": "local://libphonenumber",
            "summary": "Numbering-plan metadata; not subscriber identity.",
            "details": report["observations"][0]["details"],
        }
    ]
    assert report["observations"][0]["details"]["personal_identity_claim"] is False
    assert report["warnings"] == [
        "Licensed public-web exact-match search was temporarily unavailable."
    ]

    source_runs = {item["source"]: item for item in report["source_runs"]["records"]}
    local = source_runs["libphonenumber_metadata"]
    failed = source_runs["brave_public_web_index"]

    assert local["state"] == "executed"
    assert local["observation_count"] == 1
    assert local["execution_attempted"] is True
    assert failed["state"] == "unavailable"
    assert failed["reason"] == "remote_rate_limit"
    assert failed["observation_count"] == 0
    assert failed["execution_attempted"] is True
    assert all(item["source"] != "brave_public_web_index" for item in report["observations"])

    reopened = client.get(f"/v1/cases/{body['id']}")
    assert reopened.status_code == 200, reopened.text
    assert reopened.json()["report"] == report
