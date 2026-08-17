# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from uuid import uuid4

import pytest

from app.providers.base import ProviderQuery
from app.providers.errors import ProviderValidationError
from app.providers.gitlab_public import GitLabPublicProfileProvider


def _query(kind: str, value: str) -> ProviderQuery:
    return ProviderQuery(
        subject_id=uuid4(),
        identifier_id=uuid4(),
        identifier_kind=kind,
        identifier_value=value,
    )


@pytest.mark.asyncio
async def test_username_lookup_admits_only_public_fields_and_marks_candidate() -> None:
    async def fetcher(kind: str, value: str):
        assert (kind, value) == ("username", "alice")
        return {
            "id": 7,
            "username": "Alice",
            "name": "Alice Example",
            "public_email": "alice@example.test",
            "web_url": "https://gitlab.com/Alice",
            "organization": "Example",
            "private_email": "must-not-leak@example.test",
        }

    provider = GitLabPublicProfileProvider(fetcher=fetcher)
    result = await provider.execute(_query("username", "alice"), None)

    assert len(result.observations) == 1
    observation = result.observations[0]
    assert observation.source_locator == "https://gitlab.com/Alice"
    assert observation.payload["username"] == "Alice"
    assert observation.payload["matched_by"] == "username"
    assert observation.payload["account_candidate"] is True
    assert observation.payload["identity_claim"] is False
    assert "private_email" not in observation.payload


@pytest.mark.asyncio
async def test_exact_public_email_lookup_requires_exact_case_insensitive_match() -> None:
    async def fetcher(kind: str, value: str):
        return {
            "username": "alice",
            "public_email": "ALICE@example.test",
            "web_url": "https://gitlab.com/alice",
        }

    provider = GitLabPublicProfileProvider(fetcher=fetcher)
    result = await provider.execute(_query("email", "alice@example.test"), None)
    assert result.observations[0].payload["matched_by"] == "exact_public_email"


@pytest.mark.asyncio
async def test_mismatched_email_or_profile_url_fails_closed() -> None:
    async def wrong_email(kind: str, value: str):
        return {
            "username": "alice",
            "public_email": "other@example.test",
            "web_url": "https://gitlab.com/alice",
        }

    with pytest.raises(ProviderValidationError, match="does not match"):
        await GitLabPublicProfileProvider(fetcher=wrong_email).execute(
            _query("email", "alice@example.test"), None
        )

    async def wrong_url(kind: str, value: str):
        return {"username": "alice", "web_url": "https://evil.example/alice"}

    with pytest.raises(ProviderValidationError, match="invalid public profile URL"):
        await GitLabPublicProfileProvider(fetcher=wrong_url).execute(_query("username", "alice"), None)


@pytest.mark.asyncio
async def test_provider_rejects_credentials_and_unsupported_identifier_kinds() -> None:
    provider = GitLabPublicProfileProvider(fetcher=lambda kind, value: None)  # type: ignore[arg-type]
    with pytest.raises(ProviderValidationError, match="does not accept credentials"):
        await provider.execute(_query("username", "alice"), "secret")
    with pytest.raises(ProviderValidationError, match="usernames or public emails"):
        await provider.execute(_query("phone", "+15555550123"), None)
