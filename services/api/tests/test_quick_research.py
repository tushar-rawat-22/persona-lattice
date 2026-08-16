# SPDX-License-Identifier: Apache-2.0
from fastapi.testclient import TestClient
import pytest

from app.admin_auth import LOGIN_THROTTLE, SESSION_STORE, hash_admin_password
from app.main import app
from app.models import Purpose
from app.providers.base import ProviderObservationData, ProviderResult
from app.providers.registry import PROVIDER_BY_NAME
from app.research import ResearchKind, run_quick_research


client = TestClient(app)
PASSWORD = "synthetic-admin-password-123!"


class FakeSherlockProvider:
    descriptor = PROVIDER_BY_NAME["sherlock"]

    async def execute(self, query, secret):
        assert query.identifier_kind == "username"
        assert secret is None
        return ProviderResult(
            observations=(
                ProviderObservationData(
                    source_locator=f"https://github.com/{query.identifier_value}",
                    payload={
                        "site": "GitHub",
                        "account_state": "claimed",
                        "account_candidate": True,
                        "profile_url": f"https://github.com/{query.identifier_value}",
                        "identity_claim": False,
                    },
                ),
            )
        )


def _login(monkeypatch) -> None:
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
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_username_research_preserves_candidate_not_identity_semantics() -> None:
    report = await run_quick_research(
        kind=ResearchKind.USERNAME,
        value="@demo_user",
        purpose=Purpose.PUBLIC_SOURCE_RESEARCH,
        consent_acknowledged=False,
        sherlock_provider=FakeSherlockProvider(),
    )

    assert report.normalized_value == "demo_user"
    assert len(report.observations) == 1
    observation = report.observations[0]
    assert observation.source == "sherlock"
    assert observation.details["account_candidate"] is True
    assert observation.details["identity_claim"] is False


@pytest.mark.asyncio
async def test_phone_research_returns_numbering_metadata_not_subscriber_identity() -> None:
    report = await run_quick_research(
        kind=ResearchKind.PHONE,
        value="+91 98765 43210",
        purpose=Purpose.PUBLIC_SOURCE_RESEARCH,
        consent_acknowledged=False,
    )

    observation = report.observations[0]
    assert report.normalized_value == "+919876543210"
    assert observation.source == "libphonenumber_metadata"
    assert observation.details["country_code"] == 91
    assert observation.details["personal_identity_claim"] is False


@pytest.mark.asyncio
async def test_email_research_is_local_until_provider_is_approved() -> None:
    report = await run_quick_research(
        kind=ResearchKind.EMAIL,
        value="Test@Example.com",
        purpose=Purpose.PUBLIC_SOURCE_RESEARCH,
        consent_acknowledged=False,
    )

    assert report.normalized_value == "Test@example.com"
    assert report.observations[0].details["domain"] == "example.com"
    assert report.warnings


def test_quick_research_endpoint_requires_admin(monkeypatch) -> None:
    client.cookies.clear()
    SESSION_STORE.clear()
    monkeypatch.setenv("PERSONALATTICE_ADMIN_USERNAME", "admin")
    monkeypatch.setenv("PERSONALATTICE_ADMIN_PASSWORD_HASH", hash_admin_password(PASSWORD))
    monkeypatch.setenv("PERSONALATTICE_COOKIE_SECURE", "false")
    monkeypatch.setenv("PERSONALATTICE_SESSION_COOKIE", "personalattice_test_session")

    response = client.post(
        "/v1/research/quick",
        json={"kind": "phone", "value": "+919876543210"},
    )
    assert response.status_code == 401


def test_authenticated_phone_research_endpoint_returns_bounded_report(monkeypatch) -> None:
    _login(monkeypatch)
    response = client.post(
        "/v1/research/quick",
        json={
            "kind": "phone",
            "value": "+919876543210",
            "purpose": "public_source_research",
            "consent_acknowledged": False,
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["kind"] == "phone"
    assert body["normalized_value"] == "+919876543210"
    assert body["observations"][0]["details"]["personal_identity_claim"] is False
