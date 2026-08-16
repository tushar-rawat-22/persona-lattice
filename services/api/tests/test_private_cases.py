# SPDX-License-Identifier: Apache-2.0
from datetime import UTC, datetime, timedelta
from uuid import uuid4

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


def _login() -> None:
    response = client.post(
        "/v1/auth/login",
        json={"username": "admin", "password": PASSWORD},
    )
    assert response.status_code == 200, response.text


def _synthetic_report() -> QuickResearchReport:
    return QuickResearchReport(
        kind=ResearchKind.EMAIL,
        normalized_value="synthetic@example.test",
        observations=(
            QuickObservation(
                source="synthetic",
                source_locator="local://synthetic",
                summary="Synthetic test evidence.",
                details={"identity_claim": False},
            ),
        ),
    )


def test_case_store_round_trip_and_delete(monkeypatch, tmp_path) -> None:
    _configure(monkeypatch, tmp_path)
    now = datetime(2026, 8, 16, 10, 0, tzinfo=UTC)
    created = CASE_STORE.create(
        seed_kind=ResearchKind.EMAIL,
        seed_value="synthetic@example.test",
        report=_synthetic_report(),
        now=now,
    )

    loaded = CASE_STORE.get(created.id, now=now + timedelta(days=1))
    assert loaded is not None
    assert loaded.seed_value == "synthetic@example.test"
    assert loaded.report["observations"][0]["details"]["identity_claim"] is False
    assert CASE_STORE.delete(created.id) is True
    assert CASE_STORE.get(created.id, now=now) is None


def test_case_store_expires_and_purges(monkeypatch, tmp_path) -> None:
    _configure(monkeypatch, tmp_path)
    now = datetime(2026, 1, 1, tzinfo=UTC)
    created = CASE_STORE.create(
        seed_kind=ResearchKind.EMAIL,
        seed_value="synthetic@example.test",
        report=_synthetic_report(),
        now=now,
    )

    assert CASE_STORE.get(created.id, now=now + timedelta(days=31)) is None


def test_case_endpoints_require_admin_even_when_uuid_is_known(monkeypatch, tmp_path) -> None:
    _configure(monkeypatch, tmp_path)
    known_id = uuid4()
    assert client.get(f"/v1/cases/{known_id}").status_code == 401
    assert client.get("/v1/cases").status_code == 401
    assert client.delete(f"/v1/cases/{known_id}").status_code == 401


def test_authenticated_phone_case_is_persisted_listed_and_deletable(monkeypatch, tmp_path) -> None:
    _configure(monkeypatch, tmp_path)
    _login()

    created = client.post(
        "/v1/cases/run",
        json={
            "kind": "phone",
            "value": "+919876543210",
            "purpose": "public_source_research",
            "consent_acknowledged": False,
        },
    )
    assert created.status_code == 200, created.text
    body = created.json()
    case_id = body["id"]
    assert body["seed_kind"] == "phone"
    assert body["report"]["observations"][0]["details"]["personal_identity_claim"] is False

    listed = client.get("/v1/cases")
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [case_id]

    loaded = client.get(f"/v1/cases/{case_id}")
    assert loaded.status_code == 200
    assert loaded.json()["id"] == case_id

    deleted = client.delete(f"/v1/cases/{case_id}")
    assert deleted.status_code == 204
    assert client.get(f"/v1/cases/{case_id}").status_code == 404
