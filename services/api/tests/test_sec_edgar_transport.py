# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from email.message import Message
import json
from urllib.error import HTTPError, URLError

import pytest

from app.providers import sec_edgar_transport as sec
from app.providers.errors import (
    ProviderExecutionError,
    ProviderRemoteRateLimitError,
    ProviderResponseTooLarge,
    ProviderResultValidationError,
    ProviderTransientError,
    ProviderValidationError,
)


CIK = "0000320193"
USER_AGENT = "PersonaLattice ops@example.com"


class _Response:
    def __init__(self, raw: bytes) -> None:
        self.raw = raw

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, size: int) -> bytes:
        return self.raw[:size]


def test_transport_uses_one_exact_submissions_request_and_declared_contact() -> None:
    seen: dict[str, object] = {}
    payload = {"cik": 320193, "name": "Apple Inc."}

    def opener(request, timeout: float):
        seen["url"] = request.full_url
        seen["user_agent"] = request.get_header("User-agent")
        seen["accept"] = request.get_header("Accept")
        seen["timeout"] = timeout
        return _Response(json.dumps(payload).encode())

    result = sec._fetch_sec_submissions_sync(CIK, user_agent=USER_AGENT, opener=opener)

    assert result == payload
    assert seen == {
        "url": "https://data.sec.gov/submissions/CIK0000320193.json",
        "user_agent": USER_AGENT,
        "accept": "application/json",
        "timeout": 4.0,
    }


@pytest.mark.parametrize(
    "value",
    [
        "PersonaLattice",
        " ops@example.com",
        "ops@example.com ",
        "PersonaLattice contact.example.com",
        "x@y.z\nInjected: yes",
        "x" * 201 + "@example.com",
    ],
)
def test_user_agent_must_be_explicit_bounded_and_contactable(value: str) -> None:
    with pytest.raises(ProviderValidationError):
        sec.validate_sec_user_agent(value)


def test_transport_treats_404_as_neutral_not_found() -> None:
    def opener(request, timeout: float):
        raise HTTPError(request.full_url, 404, "missing", Message(), None)

    assert sec._fetch_sec_submissions_sync(CIK, user_agent=USER_AGENT, opener=opener) is None


def test_transport_maps_remote_rate_limit_and_retry_after() -> None:
    headers = Message()
    headers["Retry-After"] = "6"

    def opener(request, timeout: float):
        raise HTTPError(request.full_url, 429, "limited", headers, None)

    with pytest.raises(ProviderRemoteRateLimitError) as exc_info:
        sec._fetch_sec_submissions_sync(CIK, user_agent=USER_AGENT, opener=opener)
    assert exc_info.value.retry_after == 6.0


@pytest.mark.parametrize("status", [408, 500, 502, 503, 504])
def test_transport_maps_transient_http_failures(status: int) -> None:
    def opener(request, timeout: float):
        raise HTTPError(request.full_url, status, "down", Message(), None)

    with pytest.raises(ProviderTransientError):
        sec._fetch_sec_submissions_sync(CIK, user_agent=USER_AGENT, opener=opener)


def test_transport_maps_network_failure() -> None:
    def opener(request, timeout: float):
        raise URLError("offline")

    with pytest.raises(ProviderTransientError):
        sec._fetch_sec_submissions_sync(CIK, user_agent=USER_AGENT, opener=opener)


def test_transport_rejects_other_http_errors() -> None:
    def opener(request, timeout: float):
        raise HTTPError(request.full_url, 403, "blocked", Message(), None)

    with pytest.raises(ProviderExecutionError):
        sec._fetch_sec_submissions_sync(CIK, user_agent=USER_AGENT, opener=opener)


def test_transport_rejects_oversized_invalid_json_and_non_object_payload() -> None:
    with pytest.raises(ProviderResponseTooLarge):
        sec._fetch_sec_submissions_sync(
            CIK,
            user_agent=USER_AGENT,
            opener=lambda request, timeout: _Response(b"x" * (sec._MAX_RAW_RESPONSE_BYTES + 1)),
        )

    with pytest.raises(ProviderResultValidationError, match="invalid JSON"):
        sec._fetch_sec_submissions_sync(
            CIK,
            user_agent=USER_AGENT,
            opener=lambda request, timeout: _Response(b"not-json"),
        )

    with pytest.raises(ProviderResultValidationError, match="invalid response shape"):
        sec._fetch_sec_submissions_sync(
            CIK,
            user_agent=USER_AGENT,
            opener=lambda request, timeout: _Response(b"[]"),
        )
