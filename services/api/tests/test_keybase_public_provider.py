# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from email.message import Message
import json
from urllib.error import HTTPError
from uuid import uuid4

import pytest

from app.intelligence.extractor import extract_observation_leads
from app.providers import keybase_public as keybase
from app.providers.base import ProviderQuery
from app.providers.errors import (
    ProviderRemoteRateLimitError,
    ProviderResponseTooLarge,
    ProviderResultValidationError,
    ProviderTransientError,
    ProviderValidationError,
)
from app.providers.keybase_public import KeybasePublicUserProvider, keybase_username_from_seed


def _query(kind: str = "username", value: str = "maxtaco") -> ProviderQuery:
    return ProviderQuery(
        subject_id=uuid4(),
        identifier_id=uuid4(),
        identifier_kind=kind,
        identifier_value=value,
    )


def _user(username: str = "maxtaco") -> dict[str, object]:
    uid = "9a2c8a8ac48162723c7992570c87da00"
    return {
        "id": uid,
        "basics": {
            "uid": uid,
            "username": username,
            "ctime": 1399919269,
            "mtime": 1399919269,
            "track_version": 99,
        },
        "profile": {"full_name": "must not be retained"},
        "proofs_summary": {"all": ["must not be retained"]},
        "public_keys": {"primary": {"kid": "must not be retained"}},
        "cryptocurrency_addresses": {"bitcoin": ["must not be retained"]},
    }


def test_username_admission_requires_keybase_canonical_form() -> None:
    assert keybase_username_from_seed("ab") == "ab"
    assert keybase_username_from_seed("maxtaco") == "maxtaco"
    assert keybase_username_from_seed("user_123") == "user_123"
    assert keybase_username_from_seed("a123456789012345") == "a123456789012345"
    for value in (
        "a",
        "a1234567890123456",
        "_user",
        "MaxTaco",
        "user-name",
        "user.name",
        " user",
        "",
        "ümlaut",
    ):
        assert keybase_username_from_seed(value) is None


@pytest.mark.asyncio
async def test_success_retains_only_public_basics_and_emits_no_leads() -> None:
    async def fetcher(username: str) -> dict[str, object]:
        assert username == "maxtaco"
        return _user()

    result = await KeybasePublicUserProvider(fetcher=fetcher).execute(_query(), None)

    assert len(result.observations) == 1
    observation = result.observations[0]
    assert observation.source_locator == "https://keybase.io/maxtaco"
    assert observation.payload == {
        "keybase_username": "maxtaco",
        "keybase_uid": "9a2c8a8ac48162723c7992570c87da00",
        "account_created_at": 1399919269,
        "account_candidate": True,
        "identity_claim": False,
        "field_visibility": "public_directory_basics",
    }
    for excluded in ("profile", "proofs_summary", "public_keys", "cryptocurrency_addresses"):
        assert excluded not in observation.payload

    extraction = extract_observation_leads(
        details=observation.payload,
        source="keybase_public_user",
        source_locator=observation.source_locator,
    )
    assert extraction.candidates == ()


@pytest.mark.asyncio
async def test_missing_user_is_completed_zero_observation_result() -> None:
    async def fetcher(username: str) -> None:
        return None

    result = await KeybasePublicUserProvider(fetcher=fetcher).execute(_query(), None)
    assert result.observations == ()


@pytest.mark.asyncio
async def test_provider_rejects_secret_wrong_kind_and_noncanonical_username() -> None:
    provider = KeybasePublicUserProvider(fetcher=lambda username: None)  # type: ignore[arg-type]
    with pytest.raises(ProviderValidationError, match="does not accept credentials"):
        await provider.execute(_query(), "secret")
    with pytest.raises(ProviderValidationError, match="only accepts usernames"):
        await provider.execute(_query(kind="url", value="https://keybase.io/maxtaco"), None)
    with pytest.raises(ProviderValidationError, match="canonical lowercase username"):
        await provider.execute(_query(value="MaxTaco"), None)


@pytest.mark.asyncio
async def test_mismatched_username_or_uid_fails_closed() -> None:
    async def wrong_username(username: str) -> dict[str, object]:
        return _user("someone_else")

    with pytest.raises(ProviderResultValidationError, match="different username"):
        await KeybasePublicUserProvider(fetcher=wrong_username).execute(_query(), None)

    async def conflicting_uid(username: str) -> dict[str, object]:
        user = _user()
        user["id"] = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        return user

    with pytest.raises(ProviderResultValidationError, match="id fields disagree"):
        await KeybasePublicUserProvider(fetcher=conflicting_uid).execute(_query(), None)


class _Response:
    def __init__(self, raw: bytes) -> None:
        self.raw = raw

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, size: int) -> bytes:
        return self.raw[:size]


def _api_payload(user: dict[str, object] | None) -> dict[str, object]:
    return {"status": {"code": 0, "name": "OK"}, "them": [user], "csrf_token": "ignored"}


def test_transport_requests_only_basics_and_is_bounded(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, str] = {}

    def fake_urlopen(request, timeout: float):
        seen["url"] = request.full_url
        seen["user_agent"] = request.get_header("User-agent")
        assert timeout == 4.0
        return _Response(json.dumps(_api_payload(_user())).encode())

    monkeypatch.setattr(keybase, "urlopen", fake_urlopen)
    assert keybase._fetch_keybase_public_user_sync("maxtaco") == _user()
    assert "usernames=maxtaco" in seen["url"]
    assert "fields=basics" in seen["url"]
    for forbidden in ("profile", "proofs_summary", "public_keys", "cryptocurrency_addresses"):
        assert forbidden not in seen["url"]
    assert "PersonaLattice" in seen["user_agent"]


def test_transport_maps_missing_rate_limit_transient_and_oversized(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        keybase,
        "urlopen",
        lambda request, timeout: _Response(json.dumps(_api_payload(None)).encode()),
    )
    assert keybase._fetch_keybase_public_user_sync("missing") is None

    headers = Message()
    headers["Retry-After"] = "9"

    def rate_limited(request, timeout: float):
        raise HTTPError(request.full_url, 429, "limited", headers, None)

    monkeypatch.setattr(keybase, "urlopen", rate_limited)
    with pytest.raises(ProviderRemoteRateLimitError) as exc_info:
        keybase._fetch_keybase_public_user_sync("maxtaco")
    assert exc_info.value.retry_after == 9.0

    def unavailable(request, timeout: float):
        raise HTTPError(request.full_url, 503, "down", Message(), None)

    monkeypatch.setattr(keybase, "urlopen", unavailable)
    with pytest.raises(ProviderTransientError):
        keybase._fetch_keybase_public_user_sync("maxtaco")

    monkeypatch.setattr(
        keybase,
        "urlopen",
        lambda request, timeout: _Response(b"x" * (keybase._MAX_RAW_RESPONSE_BYTES + 1)),
    )
    with pytest.raises(ProviderResponseTooLarge):
        keybase._fetch_keybase_public_user_sync("maxtaco")
