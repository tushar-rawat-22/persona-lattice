# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json

import pytest

from app.providers.errors import (
    ProviderPolicyError,
    ProviderRemoteRateLimitError,
    ProviderResultValidationError,
    ProviderTransientError,
)
from app.providers.rdap_transport import PinnedHTTPSResponse, fetch_rdap_domain


BOOTSTRAP = {
    "services": [
        [["com"], ["https://rdap1.registry.example/rdap/", "https://rdap2.registry.example/rdap/"]]
    ]
}


def response(status: int, *, body: object = None, headers: dict[str, str] | None = None) -> PinnedHTTPSResponse:
    payload = b"" if body is None else json.dumps(body).encode()
    return PinnedHTTPSResponse(status=status, headers=headers or {}, body=payload)


@pytest.mark.asyncio
async def test_success_uses_fresh_public_dns_and_returns_exact_response_url() -> None:
    resolved: list[str] = []
    requested: list[tuple[str, str, str]] = []

    async def resolver(host: str) -> tuple[str, ...]:
        resolved.append(host)
        return ("93.184.216.34",)

    async def requester(host: str, ip: str, target: str) -> PinnedHTTPSResponse:
        requested.append((host, ip, target))
        return response(
            200,
            body={"objectClassName": "domain", "ldhName": "example.com"},
            headers={"content-type": "application/rdap+json; charset=utf-8"},
        )

    result = await fetch_rdap_domain(
        "example.com",
        bootstrap_payload=BOOTSTRAP,
        resolver=resolver,
        requester=requester,
    )
    assert result is not None
    assert result.canonical_query_url == "https://rdap1.registry.example/rdap/domain/example.com"
    assert result.response_url == result.canonical_query_url
    assert result.payload["ldhName"] == "example.com"
    assert resolved == ["rdap1.registry.example"]
    assert requested == [("rdap1.registry.example", "93.184.216.34", "/rdap/domain/example.com")]


@pytest.mark.asyncio
async def test_not_found_is_a_completed_empty_result() -> None:
    async def resolver(_: str) -> tuple[str, ...]:
        return ("93.184.216.34",)

    async def requester(*_: str) -> PinnedHTTPSResponse:
        return response(404)

    assert await fetch_rdap_domain(
        "example.com", bootstrap_payload=BOOTSTRAP, resolver=resolver, requester=requester
    ) is None


@pytest.mark.asyncio
async def test_rate_limit_is_not_evaded_by_falling_back_to_another_service() -> None:
    calls = 0

    async def resolver(_: str) -> tuple[str, ...]:
        return ("93.184.216.34",)

    async def requester(*_: str) -> PinnedHTTPSResponse:
        nonlocal calls
        calls += 1
        return response(429, headers={"retry-after": "7"})

    with pytest.raises(ProviderRemoteRateLimitError):
        await fetch_rdap_domain(
            "example.com", bootstrap_payload=BOOTSTRAP, resolver=resolver, requester=requester
        )
    assert calls == 1


@pytest.mark.asyncio
async def test_transient_first_authority_falls_back_to_equivalent_bootstrap_url() -> None:
    async def resolver(_: str) -> tuple[str, ...]:
        return ("93.184.216.34",)

    calls: list[str] = []

    async def requester(host: str, _: str, __: str) -> PinnedHTTPSResponse:
        calls.append(host)
        if host == "rdap1.registry.example":
            raise OSError("temporary failure")
        return response(
            200,
            body={"objectClassName": "domain", "ldhName": "example.com"},
            headers={"content-type": "application/rdap+json"},
        )

    result = await fetch_rdap_domain(
        "example.com", bootstrap_payload=BOOTSTRAP, resolver=resolver, requester=requester
    )
    assert result is not None
    assert result.canonical_query_url.startswith("https://rdap2.registry.example/")
    assert calls == ["rdap1.registry.example", "rdap2.registry.example"]


@pytest.mark.asyncio
async def test_malformed_media_type_and_json_fail_after_provider_contact() -> None:
    async def resolver(_: str) -> tuple[str, ...]:
        return ("93.184.216.34",)

    async def wrong_media(*_: str) -> PinnedHTTPSResponse:
        return response(200, body={}, headers={"content-type": "application/json"})

    with pytest.raises(ProviderResultValidationError, match="media type"):
        await fetch_rdap_domain(
            "example.com", bootstrap_payload=BOOTSTRAP, resolver=resolver, requester=wrong_media
        )

    async def bad_json(*_: str) -> PinnedHTTPSResponse:
        return PinnedHTTPSResponse(
            status=200,
            headers={"content-type": "application/rdap+json"},
            body=b"not-json",
        )

    with pytest.raises(ProviderResultValidationError, match="invalid JSON"):
        await fetch_rdap_domain(
            "example.com", bootstrap_payload=BOOTSTRAP, resolver=resolver, requester=bad_json
        )


@pytest.mark.asyncio
async def test_redirect_revalidates_dns_and_refuses_private_target() -> None:
    resolutions: list[str] = []

    async def resolver(host: str) -> tuple[str, ...]:
        resolutions.append(host)
        if host == "private.registry.example":
            return ("127.0.0.1",)
        return ("93.184.216.34",)

    async def requester(*_: str) -> PinnedHTTPSResponse:
        return response(302, headers={"location": "https://private.registry.example/rdap/domain/example.com"})

    with pytest.raises(ProviderPolicyError, match="non-global"):
        await fetch_rdap_domain(
            "example.com", bootstrap_payload=BOOTSTRAP, resolver=resolver, requester=requester
        )
    assert resolutions == ["rdap1.registry.example", "private.registry.example"]


@pytest.mark.asyncio
async def test_initial_dns_admission_refuses_private_or_excessive_answers() -> None:
    async def private_resolver(_: str) -> tuple[str, ...]:
        return ("10.0.0.1",)

    async def unused(*_: str) -> PinnedHTTPSResponse:
        raise AssertionError("requester must not run")

    with pytest.raises(ProviderPolicyError, match="non-global"):
        await fetch_rdap_domain(
            "example.com", bootstrap_payload=BOOTSTRAP, resolver=private_resolver, requester=unused
        )

    async def excessive_resolver(_: str) -> tuple[str, ...]:
        return tuple(f"93.184.216.{index}" for index in range(1, 10))

    with pytest.raises(ProviderPolicyError, match="too many"):
        await fetch_rdap_domain(
            "example.com", bootstrap_payload=BOOTSTRAP, resolver=excessive_resolver, requester=unused
        )


@pytest.mark.asyncio
async def test_all_equivalent_services_unavailable_stays_transient() -> None:
    async def resolver(_: str) -> tuple[str, ...]:
        return ("93.184.216.34",)

    async def requester(*_: str) -> PinnedHTTPSResponse:
        raise TimeoutError("timeout")

    with pytest.raises(ProviderTransientError):
        await fetch_rdap_domain(
            "example.com", bootstrap_payload=BOOTSTRAP, resolver=resolver, requester=requester
        )
