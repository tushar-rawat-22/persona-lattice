# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from uuid import uuid4

import pytest

from app.providers import ProviderQuery, ProviderValidationError
from app.providers.github_public import GitHubPublicProfileProvider


def _query(value: str = "CaseHandle", *, kind: str = "username") -> ProviderQuery:
    return ProviderQuery(
        subject_id=uuid4(),
        identifier_id=uuid4(),
        identifier_kind=kind,
        identifier_value=value,
    )


@pytest.mark.asyncio
async def test_github_provider_not_found_returns_no_observations() -> None:
    async def fetcher(_username: str):
        return None

    provider = GitHubPublicProfileProvider(fetcher=fetcher)
    result = await provider.execute(_query(), None)

    assert result.observations == ()


@pytest.mark.asyncio
async def test_github_provider_only_emits_reviewed_public_profile_fields() -> None:
    async def fetcher(username: str):
        return {
            "login": username,
            "id": 123,
            "avatar_url": "https://avatars.githubusercontent.com/u/123?v=4",
            "html_url": f"https://github.com/{username}",
            "name": "Public Name",
            "company": "Public Company",
            "blog": "https://example.test",
            "location": "Public Location",
            "email": "public@example.test",
            "hireable": True,
            "bio": "Public bio",
            "twitter_username": "public-handle",
            "public_repos": 3,
            "public_gists": 1,
            "followers": 5,
            "following": 2,
            "created_at": "2020-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
            "private_gists": 99,
            "total_private_repos": 88,
            "two_factor_authentication": True,
            "plan": {"name": "private-plan"},
        }

    provider = GitHubPublicProfileProvider(fetcher=fetcher)
    result = await provider.execute(_query(), None)

    assert len(result.observations) == 1
    observation = result.observations[0]
    assert observation.source_locator == "https://github.com/CaseHandle"
    assert observation.payload["login"] == "CaseHandle"
    assert observation.payload["email"] == "public@example.test"
    assert observation.payload["account_candidate"] is True
    assert observation.payload["identity_claim"] is False
    assert observation.payload["field_visibility"] == "public_profile_api"
    assert "private_gists" not in observation.payload
    assert "total_private_repos" not in observation.payload
    assert "two_factor_authentication" not in observation.payload
    assert "plan" not in observation.payload


@pytest.mark.asyncio
async def test_github_provider_rejects_wrong_identifier_kind() -> None:
    async def fetcher(_username: str):
        raise AssertionError("fetcher must not run")

    provider = GitHubPublicProfileProvider(fetcher=fetcher)
    with pytest.raises(ProviderValidationError, match="only accepts usernames"):
        await provider.execute(_query(kind="email"), None)


@pytest.mark.asyncio
async def test_github_provider_rejects_credentials() -> None:
    async def fetcher(_username: str):
        raise AssertionError("fetcher must not run")

    provider = GitHubPublicProfileProvider(fetcher=fetcher)
    with pytest.raises(ProviderValidationError, match="does not accept credentials"):
        await provider.execute(_query(), "secret")


@pytest.mark.asyncio
async def test_github_provider_rejects_mismatched_login() -> None:
    async def fetcher(_username: str):
        return {
            "login": "DifferentUser",
            "html_url": "https://github.com/DifferentUser",
        }

    provider = GitHubPublicProfileProvider(fetcher=fetcher)
    with pytest.raises(ProviderValidationError, match="login does not match"):
        await provider.execute(_query(), None)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "bad_url",
    [
        "http://github.com/CaseHandle",
        "https://example.test/CaseHandle",
        "https://user:pass@github.com/CaseHandle",
        "https://github.com/OtherHandle",
        "https://github.com/CaseHandle?tab=repositories",
        "https://github.com/CaseHandle#section",
    ],
)
async def test_github_provider_rejects_untrusted_profile_locator(bad_url: str) -> None:
    async def fetcher(username: str):
        return {"login": username, "html_url": bad_url}

    provider = GitHubPublicProfileProvider(fetcher=fetcher)
    with pytest.raises(ProviderValidationError, match="GitHub public profile"):
        await provider.execute(_query(), None)


@pytest.mark.asyncio
async def test_github_provider_accepts_case_insensitive_login_match_but_preserves_api_value() -> None:
    async def fetcher(_username: str):
        return {
            "login": "casehandle",
            "html_url": "https://github.com/casehandle",
        }

    provider = GitHubPublicProfileProvider(fetcher=fetcher)
    result = await provider.execute(_query("CaseHandle"), None)

    assert result.observations[0].payload["login"] == "casehandle"
