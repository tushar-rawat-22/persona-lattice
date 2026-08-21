# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from uuid import uuid4

import pytest

from app.intelligence.extractor import extract_observation_leads
from app.providers import ProviderQuery, ProviderValidationError
from app.providers.github_public import GitHubPublicProfileProvider, github_repository_from_url


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


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("https://github.com/OpenAI/openai-python", ("OpenAI", "openai-python")),
        ("https://github.com/OpenAI/openai-python/", ("OpenAI", "openai-python")),
        ("http://github.com/OpenAI/openai-python", None),
        ("https://user:pass@github.com/OpenAI/openai-python", None),
        ("https://github.com:443/OpenAI/openai-python", None),
        ("https://github.com/OpenAI/openai-python/issues", None),
        ("https://github.com/OpenAI/openai-python?tab=readme", None),
        ("https://github.com/OpenAI/openai-python#readme", None),
        ("https://github.com/OpenAI", None),
    ],
)
def test_github_repository_url_admission_is_exact(
    value: str,
    expected: tuple[str, str] | None,
) -> None:
    assert github_repository_from_url(value) == expected


@pytest.mark.asyncio
async def test_github_repository_lookup_retains_only_bounded_public_metadata_and_emits_no_leads() -> None:
    async def repository_fetcher(owner: str, repository: str):
        assert (owner, repository) == ("OpenAI", "openai-python")
        return {
            "full_name": "openai/openai-python",
            "html_url": "https://github.com/openai/openai-python",
            "private": False,
            "fork": False,
            "archived": False,
            "owner": {"login": "openai", "type": "Organization", "avatar_url": "https://example.test/avatar"},
            "description": "must not be retained",
            "homepage": "https://example.test",
            "topics": ["ai"],
            "language": "Python",
            "stargazers_count": 999,
            "watchers_count": 999,
            "forks_count": 999,
            "open_issues_count": 999,
            "created_at": "2020-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        }

    provider = GitHubPublicProfileProvider(repository_fetcher=repository_fetcher)
    result = await provider.execute(
        _query("https://github.com/OpenAI/openai-python", kind="url"),
        None,
    )

    assert len(result.observations) == 1
    observation = result.observations[0]
    assert observation.source_locator == "https://github.com/openai/openai-python"
    assert observation.payload == {
        "github_repository_full_name": "openai/openai-python",
        "github_repository_owner_login": "openai",
        "github_repository_private": False,
        "identity_claim": False,
        "field_visibility": "public_repository_api",
        "github_repository_owner_type": "Organization",
        "github_repository_fork": False,
        "github_repository_archived": False,
    }
    extracted = extract_observation_leads(
        details=dict(observation.payload),
        source="github_public_api",
        source_locator=observation.source_locator,
    )
    assert extracted.candidates == ()


@pytest.mark.asyncio
async def test_github_repository_lookup_fails_closed_on_private_or_mismatched_results() -> None:
    async def private_fetcher(_owner: str, _repository: str):
        return {
            "full_name": "openai/openai-python",
            "html_url": "https://github.com/openai/openai-python",
            "private": True,
            "owner": {"login": "openai", "type": "Organization"},
        }

    provider = GitHubPublicProfileProvider(repository_fetcher=private_fetcher)
    with pytest.raises(ProviderValidationError, match="not explicitly public"):
        await provider.execute(_query("https://github.com/openai/openai-python", kind="url"), None)

    async def mismatched_fetcher(_owner: str, _repository: str):
        return {
            "full_name": "openai/different",
            "html_url": "https://github.com/openai/different",
            "private": False,
            "owner": {"login": "openai", "type": "Organization"},
        }

    provider = GitHubPublicProfileProvider(repository_fetcher=mismatched_fetcher)
    with pytest.raises(ProviderValidationError, match="full_name does not match"):
        await provider.execute(_query("https://github.com/openai/openai-python", kind="url"), None)
