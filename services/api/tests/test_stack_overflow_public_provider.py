# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from email.message import Message
import gzip
from io import BytesIO
import json
from urllib.error import HTTPError
from uuid import uuid4

import pytest

from app.intelligence.extractor import extract_observation_leads
from app.providers.base import ProviderQuery
from app.providers.errors import (
    ProviderRemoteRateLimitError,
    ProviderResultValidationError,
    ProviderTransientError,
    ProviderValidationError,
)
from app.providers import stack_overflow_public as stack_overflow
from app.providers.stack_overflow_public import (
    StackOverflowPublicProfileProvider,
    stack_overflow_user_id_from_url,
)


def _query(
    kind: str = "url",
    value: str = "https://stackoverflow.com/users/12345/example-user",
) -> ProviderQuery:
    return ProviderQuery(
        subject_id=uuid4(),
        identifier_id=uuid4(),
        identifier_kind=kind,
        identifier_value=value,
    )


def _profile_payload(user_id: int = 12345) -> dict[str, object]:
    return {
        "items": [
            {
                "user_id": user_id,
                "display_name": "Example User",
                "reputation": 4321,
                "creation_date": 1_700_000_000,
                "link": f"https://stackoverflow.com/users/{user_id}/example-user",
                "location": "not retained",
                "website_url": "https://should-not-be-retained.example/",
                "profile_image": "https://should-not-be-retained.example/avatar.png",
            }
        ],
        "quota_remaining": 9999,
    }


def test_profile_url_admission_is_exact_and_numeric() -> None:
    assert stack_overflow_user_id_from_url("https://stackoverflow.com/users/12345/example-user") == 12345
    assert stack_overflow_user_id_from_url("http://stackoverflow.com/users/12345") == 12345
    assert stack_overflow_user_id_from_url("https://stackoverflow.com/users/12345/example-user?tab=profile") == 12345

    for value in (
        "https://stackoverflow.com/users",
        "https://stackoverflow.com/users/0/example",
        "https://stackoverflow.com/users/not-an-id/example",
        "https://stackoverflow.com/users/12345/example/extra",
        "https://stackoverflow.com/search?q=example",
        "https://stackoverflow.com:8443/users/12345/example",
        "https://www.stackoverflow.com/users/12345/example",
        "https://stackexchange.com/users/12345/example",
        "https://user:secret@stackoverflow.com/users/12345/example",
        "javascript:alert(1)",
    ):
        assert stack_overflow_user_id_from_url(value) is None


@pytest.mark.asyncio
async def test_success_retains_only_bounded_prefixed_metadata_and_emits_no_leads() -> None:
    async def fetcher(user_id: int) -> dict[str, object]:
        assert user_id == 12345
        return _profile_payload()

    result = await StackOverflowPublicProfileProvider(fetcher=fetcher).execute(_query(), None)

    assert len(result.observations) == 1
    observation = result.observations[0]
    assert observation.source_locator == "https://stackoverflow.com/users/12345/example-user"
    assert observation.payload == {
        "stack_overflow_user_id": 12345,
        "stack_overflow_display_name": "Example User",
        "stack_overflow_reputation": 4321,
        "stack_overflow_creation_unix": 1_700_000_000,
        "api_attribution": "Stack Overflow",
        "identity_claim": False,
    }
    assert "location" not in observation.payload
    assert "website_url" not in observation.payload
    assert "profile_image" not in observation.payload

    extraction = extract_observation_leads(
        details=observation.payload,
        source="stack_overflow_public_profile",
        source_locator=observation.source_locator,
    )
    assert extraction.candidates == ()


@pytest.mark.asyncio
async def test_missing_user_is_completed_zero_observation_result() -> None:
    async def fetcher(user_id: int) -> dict[str, object]:
        return {"items": []}

    result = await StackOverflowPublicProfileProvider(fetcher=fetcher).execute(_query(), None)
    assert result.observations == ()


@pytest.mark.asyncio
async def test_provider_rejects_credentials_wrong_kind_and_non_profile_url() -> None:
    provider = StackOverflowPublicProfileProvider(fetcher=lambda user_id: None)  # type: ignore[arg-type]
    with pytest.raises(ProviderValidationError, match="does not accept credentials"):
        await provider.execute(_query(), "secret")
    with pytest.raises(ProviderValidationError, match="only accepts URLs"):
        await provider.execute(_query(kind="username", value="example"), None)
    with pytest.raises(ProviderValidationError, match="requires an exact profile URL"):
        await provider.execute(_query(value="https://stackoverflow.com/questions/123/example"), None)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload, message",
    [
        ({}, "missing items"),
        ({"items": [{"user_id": 999, "display_name": "X", "reputation": 1, "creation_date": 1, "link": "https://stackoverflow.com/users/999/x"}]}, "different user id"),
        ({"items": [{"user_id": 12345, "display_name": "X", "reputation": 1, "creation_date": 1, "link": "https://evil.example/users/12345/x"}]}, "invalid canonical link"),
        ({"items": [{"user_id": 12345, "display_name": "X", "reputation": True, "creation_date": 1, "link": "https://stackoverflow.com/users/12345/x"}]}, "invalid reputation"),
    ],
)
async def test_malformed_exact_user_results_fail_closed(payload: dict[str, object], message: str) -> None:
    async def fetcher(user_id: int) -> dict[str, object]:
        return payload

    with pytest.raises(ProviderResultValidationError, match=message):
        await StackOverflowPublicProfileProvider(fetcher=fetcher).execute(_query(), None)


@pytest.mark.asyncio
async def test_api_backoff_is_preserved_as_remote_rate_limit() -> None:
    async def fetcher(user_id: int) -> dict[str, object]:
        return {"backoff": 7, "items": []}

    with pytest.raises(ProviderRemoteRateLimitError) as exc_info:
        await StackOverflowPublicProfileProvider(fetcher=fetcher).execute(_query(), None)
    assert exc_info.value.retry_after == 7.0


class _Response:
    def __init__(self, raw: bytes, *, content_encoding: str = "") -> None:
        self.raw = raw
        self.headers = Message()
        if content_encoding:
            self.headers["Content-Encoding"] = content_encoding

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, size: int) -> bytes:
        return self.raw[:size]


def _gzip_bytes(raw: bytes) -> bytes:
    target = BytesIO()
    with gzip.GzipFile(fileobj=target, mode="wb") as stream:
        stream.write(raw)
    return target.getvalue()


def test_transport_uses_exact_user_endpoint_site_and_descriptive_user_agent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, str] = {}

    def fake_urlopen(request, timeout: float):
        seen["url"] = request.full_url
        seen["user_agent"] = request.get_header("User-agent")
        assert timeout == 4.0
        return _Response(json.dumps({"items": []}).encode())

    monkeypatch.setattr(stack_overflow, "urlopen", fake_urlopen)
    payload = stack_overflow._fetch_stack_overflow_profile_sync(12345)

    assert payload == {"items": []}
    assert seen["url"] == "https://api.stackexchange.com/2.3/users/12345?site=stackoverflow"
    assert seen["user_agent"] == "PersonaLattice/0.0.1 stack-overflow-profile-research"
    assert "inname" not in seen["url"]


def test_transport_handles_bounded_gzip_response(monkeypatch: pytest.MonkeyPatch) -> None:
    encoded = _gzip_bytes(json.dumps({"items": []}).encode())
    monkeypatch.setattr(
        stack_overflow,
        "urlopen",
        lambda request, timeout: _Response(encoded, content_encoding="gzip"),
    )
    assert stack_overflow._fetch_stack_overflow_profile_sync(12345) == {"items": []}


def test_transport_maps_429_and_retry_after(monkeypatch: pytest.MonkeyPatch) -> None:
    headers = Message()
    headers["Retry-After"] = "9"

    def fake_urlopen(request, timeout: float):
        raise HTTPError(request.full_url, 429, "rate limited", headers, None)

    monkeypatch.setattr(stack_overflow, "urlopen", fake_urlopen)
    with pytest.raises(ProviderRemoteRateLimitError) as exc_info:
        stack_overflow._fetch_stack_overflow_profile_sync(12345)
    assert exc_info.value.retry_after == 9.0


def test_transport_maps_transient_and_oversized_results(monkeypatch: pytest.MonkeyPatch) -> None:
    def unavailable(request, timeout: float):
        raise HTTPError(request.full_url, 503, "unavailable", Message(), None)

    monkeypatch.setattr(stack_overflow, "urlopen", unavailable)
    with pytest.raises(ProviderTransientError):
        stack_overflow._fetch_stack_overflow_profile_sync(12345)

    monkeypatch.setattr(
        stack_overflow,
        "urlopen",
        lambda request, timeout: _Response(b"x" * (stack_overflow._MAX_RAW_RESPONSE_BYTES + 1)),
    )
    with pytest.raises(ProviderResultValidationError, match="exceeded the adapter limit"):
        stack_overflow._fetch_stack_overflow_profile_sync(12345)
