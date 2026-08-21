# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from urllib.parse import parse_qs, urlsplit
from uuid import uuid4

import pytest

from app.providers.base import ProviderQuery
from app.providers.errors import ProviderValidationError
from app.providers.gitlab_public import (
    GitLabPublicProfileProvider,
    fetch_gitlab_public,
    gitlab_profile_username_from_url,
)
import app.providers.gitlab_public as gitlab_module


def _query(value: str) -> ProviderQuery:
    return ProviderQuery(
        subject_id=uuid4(),
        identifier_id=uuid4(),
        identifier_kind="url",
        identifier_value=value,
    )


def test_exact_profile_url_admission_is_canonical_and_route_safe() -> None:
    assert gitlab_profile_username_from_url("https://gitlab.com/Alice") == "Alice"
    assert gitlab_profile_username_from_url("https://gitlab.com/Alice/") == "Alice"

    rejected = (
        "http://gitlab.com/Alice",
        "https://user:pass@gitlab.com/Alice",
        "https://gitlab.com:443/Alice",
        "https://gitlab.com/Alice?tab=activity",
        "https://gitlab.com/Alice#bio",
        "https://gitlab.com/%41lice",
        "https://gitlab.com/Alice/project",
        "https://gitlab.com/-/u/123",
        "https://gitlab.com/search",
        "https://gitlab.com/groups",
        "https://gitlab.com/health_check",
        "https://gitlab.com/404.html",
        "https://example.com/Alice",
    )
    assert all(gitlab_profile_username_from_url(value) is None for value in rejected)


@pytest.mark.asyncio
async def test_profile_url_transport_reuses_human_only_username_lookup(monkeypatch) -> None:
    requested_urls: list[str] = []

    class _Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self, _limit: int) -> bytes:
            return b'[{"username":"Alice","web_url":"https://gitlab.com/Alice"}]'

    def fake_urlopen(request, timeout: float):
        assert timeout == 4.0
        requested_urls.append(request.full_url)
        return _Response()

    monkeypatch.setattr(gitlab_module, "urlopen", fake_urlopen)

    payload = await fetch_gitlab_public("url", "https://gitlab.com/Alice")
    assert payload is not None
    assert payload["username"] == "Alice"
    assert len(requested_urls) == 1
    query = parse_qs(urlsplit(requested_urls[0]).query)
    assert query == {"username": ["Alice"], "humans": ["true"]}


@pytest.mark.asyncio
async def test_exact_profile_url_reuses_reviewed_person_observation() -> None:
    calls: list[tuple[str, str]] = []

    async def fetcher(kind: str, value: str):
        calls.append((kind, value))
        return {
            "id": 7,
            "username": "Alice",
            "name": "Alice Example",
            "web_url": "https://gitlab.com/Alice",
            "private_email": "must-not-leak@example.test",
        }

    provider = GitLabPublicProfileProvider(fetcher=fetcher)
    result = await provider.execute(_query("https://gitlab.com/Alice"), None)

    assert calls == [("url", "https://gitlab.com/Alice")]
    assert len(result.observations) == 1
    observation = result.observations[0]
    assert observation.source_locator == "https://gitlab.com/Alice"
    assert observation.payload["username"] == "Alice"
    assert observation.payload["matched_by"] == "exact_profile_url"
    assert observation.payload["account_candidate"] is True
    assert observation.payload["identity_claim"] is False
    assert "private_email" not in observation.payload


@pytest.mark.asyncio
async def test_one_segment_group_or_missing_human_is_clean_no_match() -> None:
    async def no_human(kind: str, value: str):
        assert (kind, value) == ("url", "https://gitlab.com/example-group")
        return None

    provider = GitLabPublicProfileProvider(fetcher=no_human)
    result = await provider.execute(_query("https://gitlab.com/example-group"), None)
    assert result.observations == ()


@pytest.mark.asyncio
async def test_profile_url_response_mismatch_fails_closed() -> None:
    async def wrong_username(kind: str, value: str):
        return {"username": "Bob", "web_url": "https://gitlab.com/Bob"}

    provider = GitLabPublicProfileProvider(fetcher=wrong_username)
    with pytest.raises(ProviderValidationError, match="username does not match"):
        await provider.execute(_query("https://gitlab.com/Alice"), None)

    async def wrong_locator(kind: str, value: str):
        return {"username": "Alice", "web_url": "https://gitlab.com/Other"}

    provider = GitLabPublicProfileProvider(fetcher=wrong_locator)
    with pytest.raises(ProviderValidationError, match="invalid public profile URL"):
        await provider.execute(_query("https://gitlab.com/Alice"), None)
