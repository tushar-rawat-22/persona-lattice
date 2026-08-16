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


async def _none(_value: str):
    return None


async def _github_profile(username: str):
    return {
        "login": username,
        "id": 42,
        "html_url": f"https://github.com/{username}",
        "avatar_url": "https://avatars.example.test/42",
        "name": "Synthetic Person",
        "company": "Example Org",
        "blog": "https://example.test",
        "location": "Example City",
        "email": "public@example.test",
        "bio": "Synthetic public bio",
        "twitter_username": "synthetic_twitter",
        "public_repos": 7,
        "private_field": "must-not-leak",
    }


async def _gitlab_profile(username: str):
    return {
        "id": 43,
        "username": username,
        "name": "Synthetic GitLab Person",
        "state": "active",
        "avatar_url": "https://gitlab.example.test/avatar",
        "web_url": f"https://gitlab.com/{username}",
        "location": "GitLab City",
        "public_email": "public@example.test",
        "website_url": "https://example.test/gitlab",
        "organization": "GitLab Org",
        "private_field": "must-not-leak",
    }


async def _codeforces_profile(handle: str):
    return {
        "handle": handle,
        "firstName": "Synthetic",
        "lastName": "Coder",
        "country": "Testland",
        "city": "Code City",
        "organization": "Contest Org",
        "rating": 1700,
        "avatar": "https://codeforces.example.test/avatar",
        "private_field": "must-not-leak",
    }


async def _gitlab_email_profile(email: str):
    return {
        "id": 44,
        "username": "email-match-user",
        "name": "Public Email Profile",
        "web_url": "https://gitlab.com/email-match-user",
        "public_email": email,
        "organization": "Example Org",
    }


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
    assert response.status_code == 200
    return response.json()["csrf_token"]


@pytest.mark.asyncio
async def test_username_research_preserves_candidate_not_identity_semantics() -> None:
    report = await run_quick_research(
        kind=ResearchKind.USERNAME,
        value="@demo_user",
        purpose=Purpose.PUBLIC_SOURCE_RESEARCH,
        consent_acknowledged=False,
        sherlock_provider=FakeSherlockProvider(),
        github_lookup=_none,
        gitlab_lookup=_none,
        codeforces_lookup=_none,
    )

    assert report.normalized_value == "demo_user"
    assert len(report.observations) == 1
    assert report.observations[0].details["account_candidate"] is True
    assert report.observations[0].details["identity_claim"] is False


@pytest.mark.asyncio
async def test_username_research_enriches_allowlisted_public_profile_fields() -> None:
    report = await run_quick_research(
        kind=ResearchKind.USERNAME,
        value="@demo_user",
        purpose=Purpose.PUBLIC_SOURCE_RESEARCH,
        consent_acknowledged=False,
        sherlock_provider=FakeSherlockProvider(),
        github_lookup=_github_profile,
        gitlab_lookup=_gitlab_profile,
        codeforces_lookup=_codeforces_profile,
    )

    sources = {item.source: item for item in report.observations}
    assert {"github_public_api", "gitlab_public_api", "codeforces_public_api"}.issubset(sources)
    assert sources["github_public_api"].details["email"] == "public@example.test"
    assert sources["gitlab_public_api"].details["public_email"] == "public@example.test"
    assert sources["codeforces_public_api"].details["city"] == "Code City"
    for source in ("github_public_api", "gitlab_public_api", "codeforces_public_api"):
        assert sources[source].details["account_candidate"] is True
        assert sources[source].details["identity_claim"] is False
        assert "private_field" not in sources[source].details


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
async def test_email_research_can_match_exact_public_gitlab_email() -> None:
    report = await run_quick_research(
        kind=ResearchKind.EMAIL,
        value="Test@Example.com",
        purpose=Purpose.PUBLIC_SOURCE_RESEARCH,
        consent_acknowledged=False,
        gitlab_email_lookup=_gitlab_email_profile,
    )

    assert report.normalized_value == "Test@example.com"
    gitlab = next(item for item in report.observations if item.source == "gitlab_public_api")
    assert gitlab.details["public_email"] == "Test@example.com"
    assert gitlab.details["matched_by"] == "exact_public_email"
    assert gitlab.details["identity_claim"] is False


@pytest.mark.asyncio
async def test_email_research_refuses_owner_inference_without_public_match() -> None:
    report = await run_quick_research(
        kind=ResearchKind.EMAIL,
        value="Test@Example.com",
        purpose=Purpose.PUBLIC_SOURCE_RESEARCH,
        consent_acknowledged=False,
        gitlab_email_lookup=_none,
    )
    assert len(report.observations) == 1
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
    csrf = _login(monkeypatch)
    response = client.post(
        "/v1/research/quick",
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
    assert body["kind"] == "phone"
    assert body["normalized_value"] == "+919876543210"
    assert body["observations"][0]["details"]["personal_identity_claim"] is False
