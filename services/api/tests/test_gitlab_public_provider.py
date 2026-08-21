# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from urllib.parse import parse_qs, urlsplit
from uuid import uuid4

import pytest

from app.providers.base import ProviderQuery
from app.providers.errors import ProviderValidationError
from app.providers.gitlab_public import GitLabPublicProfileProvider, gitlab_project_path_from_url
import app.providers.gitlab_public as gitlab_module


def _query(kind: str, value: str) -> ProviderQuery:
    return ProviderQuery(
        subject_id=uuid4(),
        identifier_id=uuid4(),
        identifier_kind=kind,
        identifier_value=value,
    )


@pytest.mark.parametrize(
    ("kind", "value", "parameter"),
    [
        ("username", "Alice", "username"),
        ("email", "alice@example.test", "public_email"),
    ],
)
def test_person_profile_transport_always_requests_human_users(
    monkeypatch,
    kind: str,
    value: str,
    parameter: str,
) -> None:
    requested_urls: list[str] = []

    class _Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self, _limit: int) -> bytes:
            return b"[]"

    def fake_urlopen(request, timeout: float):
        assert timeout == 4.0
        requested_urls.append(request.full_url)
        return _Response()

    monkeypatch.setattr(gitlab_module, "urlopen", fake_urlopen)

    assert gitlab_module._fetch_gitlab_public_profile_sync(kind, value) is None
    assert len(requested_urls) == 1
    query = parse_qs(urlsplit(requested_urls[0]).query)
    assert query == {parameter: [value], "humans": ["true"]}


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


def test_project_url_admission_is_exact_and_excludes_subgroups_and_routes() -> None:
    assert (
        gitlab_project_path_from_url("https://gitlab.com/example/project")
        == "example/project"
    )
    rejected = (
        "http://gitlab.com/example/project",
        "https://user:pass@gitlab.com/example/project",
        "https://gitlab.com:443/example/project",
        "https://gitlab.com/example/project?x=1",
        "https://gitlab.com/example/project#readme",
        "https://gitlab.com/example/project.git",
        "https://gitlab.com/example/project/issues",
        "https://gitlab.com/group/subgroup/project",
        "https://example.com/example/project",
    )
    assert all(gitlab_project_path_from_url(value) is None for value in rejected)


@pytest.mark.asyncio
async def test_exact_public_project_retains_only_bounded_display_metadata() -> None:
    async def fetcher(kind: str, value: str):
        assert (kind, value) == ("url", "https://gitlab.com/example/project")
        return {
            "id": 42,
            "name": "Project",
            "path": "project",
            "path_with_namespace": "example/project",
            "visibility": "public",
            "archived": False,
            "web_url": "https://gitlab.com/example/project",
            "namespace": {
                "kind": "group",
                "full_path": "example",
                "name": "Example Group",
                "avatar_url": "https://gitlab.com/uploads/secret.png",
            },
            "description": "must not be retained",
            "star_count": 999,
            "forks_count": 50,
            "topics": ["identity"],
            "owner": {"username": "must-not-become-a-lead"},
        }

    provider = GitLabPublicProfileProvider(fetcher=fetcher)
    result = await provider.execute(
        _query("url", "https://gitlab.com/example/project"),
        None,
    )

    assert len(result.observations) == 1
    observation = result.observations[0]
    assert observation.source_locator == "https://gitlab.com/example/project"
    assert observation.payload == {
        "gitlab_project_id": 42,
        "gitlab_project_path_with_namespace": "example/project",
        "gitlab_project_visibility": "public",
        "gitlab_project_namespace_kind": "group",
        "gitlab_project_namespace_full_path": "example",
        "gitlab_project_archived": False,
        "identity_claim": False,
        "field_visibility": "public_project_api",
        "matched_by": "exact_project_url",
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload, message",
    [
        (
            {
                "id": 42,
                "path_with_namespace": "other/project",
                "visibility": "public",
                "web_url": "https://gitlab.com/other/project",
                "namespace": {"kind": "group", "full_path": "other"},
            },
            "path does not match",
        ),
        (
            {
                "id": 42,
                "path_with_namespace": "example/project",
                "visibility": "private",
                "web_url": "https://gitlab.com/example/project",
                "namespace": {"kind": "group", "full_path": "example"},
            },
            "non-public",
        ),
        (
            {
                "id": 42,
                "path_with_namespace": "example/project",
                "visibility": "public",
                "web_url": "https://evil.example/example/project",
                "namespace": {"kind": "group", "full_path": "example"},
            },
            "invalid canonical project URL",
        ),
        (
            {
                "id": 42,
                "path_with_namespace": "example/project",
                "visibility": "public",
                "web_url": "https://gitlab.com/example/project",
                "namespace": {"kind": "instance", "full_path": "example"},
            },
            "invalid namespace kind",
        ),
    ],
)
async def test_project_response_mismatch_or_non_public_state_fails_closed(
    payload: dict[str, object],
    message: str,
) -> None:
    async def fetcher(kind: str, value: str):
        return payload

    provider = GitLabPublicProfileProvider(fetcher=fetcher)
    with pytest.raises(ProviderValidationError, match=message):
        await provider.execute(_query("url", "https://gitlab.com/example/project"), None)


@pytest.mark.asyncio
async def test_provider_rejects_credentials_and_unsupported_identifier_kinds() -> None:
    provider = GitLabPublicProfileProvider(fetcher=lambda kind, value: None)  # type: ignore[arg-type]
    with pytest.raises(ProviderValidationError, match="does not accept credentials"):
        await provider.execute(_query("username", "alice"), "secret")
    with pytest.raises(ProviderValidationError, match="usernames, public emails, or exact project URLs"):
        await provider.execute(_query("phone", "+15555550123"), None)