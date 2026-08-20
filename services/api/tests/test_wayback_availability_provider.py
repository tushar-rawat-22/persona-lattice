# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from email.message import Message
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
from app.providers import wayback_availability as wayback
from app.providers.wayback_availability import WaybackAvailabilityProvider


def _query(kind: str = "url", value: str = "https://example.com/path") -> ProviderQuery:
    return ProviderQuery(
        subject_id=uuid4(),
        identifier_id=uuid4(),
        identifier_kind=kind,
        identifier_value=value,
    )


def _capture_payload() -> dict[str, object]:
    return {
        "archived_snapshots": {
            "closest": {
                "available": True,
                "status": "200",
                "timestamp": "20260102030405",
                "url": "https://web.archive.org/web/20260102030405/https://example.com/path",
            }
        }
    }


@pytest.mark.asyncio
async def test_capture_retains_metadata_only_and_emits_no_leads() -> None:
    async def fetcher(value: str) -> dict[str, object]:
        assert value == "https://example.com/path"
        return _capture_payload()

    result = await WaybackAvailabilityProvider(fetcher=fetcher).execute(_query(), None)

    assert len(result.observations) == 1
    observation = result.observations[0]
    assert observation.source_locator == (
        "https://web.archive.org/web/20260102030405/https://example.com/path"
    )
    assert observation.payload == {
        "queried_url": "https://example.com/path",
        "capture_available": True,
        "capture_status": "200",
        "capture_timestamp": "20260102030405",
        "archived_content_fetched": False,
        "identity_claim": False,
    }
    extraction = extract_observation_leads(
        details=observation.payload,
        source="wayback_url_availability",
        source_locator=observation.source_locator,
    )
    assert extraction.candidates == ()


@pytest.mark.asyncio
async def test_no_capture_is_completed_zero_observation_result() -> None:
    async def fetcher(value: str) -> dict[str, object]:
        return {"archived_snapshots": {}}

    result = await WaybackAvailabilityProvider(fetcher=fetcher).execute(_query(), None)
    assert result.observations == ()


@pytest.mark.asyncio
async def test_provider_rejects_credentials_wrong_kind_and_bad_snapshot_locator() -> None:
    async def fetcher(value: str) -> dict[str, object]:
        payload = _capture_payload()
        closest = payload["archived_snapshots"]["closest"]  # type: ignore[index]
        closest["url"] = "https://evil.example/web/20260102030405/https://example.com/path"  # type: ignore[index]
        return payload

    provider = WaybackAvailabilityProvider(fetcher=fetcher)
    with pytest.raises(ProviderValidationError, match="does not accept credentials"):
        await provider.execute(_query(), "secret")
    with pytest.raises(ProviderValidationError, match="only accepts URLs"):
        await provider.execute(_query(kind="username", value="example"), None)
    with pytest.raises(ProviderResultValidationError, match="invalid snapshot locator"):
        await provider.execute(_query(), None)


@pytest.mark.asyncio
async def test_malformed_capture_fields_fail_closed_after_provider_attempt() -> None:
    async def bad_timestamp(value: str) -> dict[str, object]:
        payload = _capture_payload()
        closest = payload["archived_snapshots"]["closest"]  # type: ignore[index]
        closest["timestamp"] = "yesterday"  # type: ignore[index]
        return payload

    with pytest.raises(ProviderResultValidationError, match="invalid timestamp"):
        await WaybackAvailabilityProvider(fetcher=bad_timestamp).execute(_query(), None)


class _Response:
    def __init__(self, raw: bytes) -> None:
        self.raw = raw

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, size: int) -> bytes:
        return self.raw[:size]


def test_transport_sends_descriptive_user_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, str] = {}

    def fake_urlopen(request, timeout: float):
        seen["user_agent"] = request.get_header("User-agent")
        seen["url"] = request.full_url
        assert timeout == 4.0
        return _Response(json.dumps({"archived_snapshots": {}}).encode())

    monkeypatch.setattr(wayback, "urlopen", fake_urlopen)
    payload = wayback._fetch_wayback_availability_sync("https://example.com/a b")

    assert payload == {"archived_snapshots": {}}
    assert seen["user_agent"] == "PersonaLattice/0.0.1 wayback-availability-research"
    assert seen["url"].startswith("https://archive.org/wayback/available?")
    assert "url=https%3A%2F%2Fexample.com%2Fa+b" in seen["url"]


def test_transport_maps_429_and_retry_after(monkeypatch: pytest.MonkeyPatch) -> None:
    headers = Message()
    headers["Retry-After"] = "7"

    def fake_urlopen(request, timeout: float):
        raise HTTPError(request.full_url, 429, "rate limited", headers, None)

    monkeypatch.setattr(wayback, "urlopen", fake_urlopen)
    with pytest.raises(ProviderRemoteRateLimitError) as exc_info:
        wayback._fetch_wayback_availability_sync("https://example.com/")
    assert exc_info.value.retry_after == 7


def test_transport_maps_transient_and_oversized_results(monkeypatch: pytest.MonkeyPatch) -> None:
    def unavailable(request, timeout: float):
        raise HTTPError(request.full_url, 503, "unavailable", Message(), None)

    monkeypatch.setattr(wayback, "urlopen", unavailable)
    with pytest.raises(ProviderTransientError):
        wayback._fetch_wayback_availability_sync("https://example.com/")

    monkeypatch.setattr(
        wayback,
        "urlopen",
        lambda request, timeout: _Response(b"x" * (wayback._MAX_RAW_RESPONSE_BYTES + 1)),
    )
    with pytest.raises(ProviderResultValidationError, match="exceeded the adapter limit"):
        wayback._fetch_wayback_availability_sync("https://example.com/")
