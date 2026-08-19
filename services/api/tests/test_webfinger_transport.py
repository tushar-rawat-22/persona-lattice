# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import pytest

from app.providers.errors import (
    ProviderPolicyError,
    ProviderRemoteRateLimitError,
    ProviderResultValidationError,
    ProviderTransientError,
)
from app.providers.webfinger_admission import WebFingerAdmissionError, webfinger_network_target
from app.providers.webfinger_transport import PinnedHTTPSResponse, fetch_webfinger_jrd


class FakeTransport:
    def __init__(
        self,
        *,
        dns: dict[str, tuple[str, ...]],
        responses: list[PinnedHTTPSResponse],
    ) -> None:
        self.dns = dns
        self.responses = list(responses)
        self.resolutions: list[str] = []
        self.requests: list[tuple[str, str, str]] = []

    async def resolve(self, hostname: str) -> tuple[str, ...]:
        self.resolutions.append(hostname)
        return self.dns.get(hostname, ())

    async def request(
        self,
        hostname: str,
        connect_ip: str,
        request_target: str,
    ) -> PinnedHTTPSResponse:
        self.requests.append((hostname, connect_ip, request_target))
        if not self.responses:
            raise AssertionError("unexpected WebFinger request")
        return self.responses.pop(0)


def response(
    status: int,
    *,
    body: bytes = b"",
    headers: dict[str, str] | None = None,
) -> PinnedHTTPSResponse:
    return PinnedHTTPSResponse(status=status, headers=headers or {}, body=body)


@pytest.mark.parametrize(
    "target",
    [
        "http://wf.example/service?resource=x",
        "https://127.0.0.1/service?resource=x",
        "https://localhost/service?resource=x",
        "https://user@wf.example/service?resource=x",
        "https://wf.example:8443/service?resource=x",
        "https://wf.example/service?resource=x#fragment",
        "https://wf.example/service?resource=x\nX-Test: injected",
    ],
)
def test_redirect_target_admission_rejects_unsafe_https_targets(target: str) -> None:
    with pytest.raises(WebFingerAdmissionError):
        webfinger_network_target(target, allow_query=True)


def test_redirect_target_allows_bounded_https_query() -> None:
    target = webfinger_network_target(
        "https://wf.example/hosted/webfinger?resource=https%3A%2F%2Fsocial.example%2F%40alice",
        allow_query=True,
    )
    assert target.hostname == "wf.example"
    assert target.request_target == (
        "/hosted/webfinger?resource=https%3A%2F%2Fsocial.example%2F%40alice"
    )


@pytest.mark.asyncio
async def test_success_uses_fresh_dns_and_pins_https_to_admitted_ip() -> None:
    fake = FakeTransport(
        dns={"social.example": ("93.184.216.34",)},
        responses=[
            response(
                200,
                body=b'{"subject":"https://social.example/@alice","links":[]}',
                headers={"content-type": "application/jrd+json"},
            )
        ],
    )

    payload = await fetch_webfinger_jrd(
        "https://social.example/@alice",
        resolver=fake.resolve,
        requester=fake.request,
    )

    assert payload == {"subject": "https://social.example/@alice", "links": []}
    assert fake.resolutions == ["social.example"]
    assert fake.requests == [
        (
            "social.example",
            "93.184.216.34",
            "/.well-known/webfinger?resource=https%3A%2F%2Fsocial.example%2F%40alice",
        )
    ]


@pytest.mark.asyncio
async def test_initial_private_or_unroutable_dns_fails_before_provider_contact() -> None:
    fake = FakeTransport(
        dns={"social.example": ("10.0.0.8",)},
        responses=[],
    )

    with pytest.raises(ProviderPolicyError, match="non-global"):
        await fetch_webfinger_jrd(
            "https://social.example/@alice",
            resolver=fake.resolve,
            requester=fake.request,
        )

    assert fake.requests == []


@pytest.mark.asyncio
async def test_redirect_is_revalidated_resolved_again_and_pinned_to_new_host() -> None:
    fake = FakeTransport(
        dns={
            "social.example": ("93.184.216.34",),
            "wf.example": ("142.250.72.14",),
        },
        responses=[
            response(
                307,
                headers={
                    "location": (
                        "https://wf.example/hosted/webfinger?"
                        "resource=https%3A%2F%2Fsocial.example%2F%40alice"
                    )
                },
            ),
            response(
                200,
                body=b'{"subject":"https://social.example/@alice","links":[]}',
                headers={"content-type": "application/jrd+json; charset=utf-8"},
            ),
        ],
    )

    payload = await fetch_webfinger_jrd(
        "https://social.example/@alice",
        resolver=fake.resolve,
        requester=fake.request,
    )

    assert payload is not None
    assert fake.resolutions == ["social.example", "wf.example"]
    assert [item[:2] for item in fake.requests] == [
        ("social.example", "93.184.216.34"),
        ("wf.example", "142.250.72.14"),
    ]


@pytest.mark.asyncio
async def test_redirect_to_private_target_is_malformed_result_after_contact() -> None:
    fake = FakeTransport(
        dns={"social.example": ("93.184.216.34",)},
        responses=[response(307, headers={"location": "https://127.0.0.1/webfinger"})],
    )

    with pytest.raises(ProviderResultValidationError):
        await fetch_webfinger_jrd(
            "https://social.example/@alice",
            resolver=fake.resolve,
            requester=fake.request,
        )

    assert len(fake.requests) == 1


@pytest.mark.asyncio
async def test_redirect_host_without_public_resolution_is_malformed_after_contact() -> None:
    fake = FakeTransport(
        dns={
            "social.example": ("93.184.216.34",),
            "wf.example": (),
        },
        responses=[response(307, headers={"location": "https://wf.example/webfinger?resource=x"})],
    )

    with pytest.raises(ProviderResultValidationError, match="redirect target"):
        await fetch_webfinger_jrd(
            "https://social.example/@alice",
            resolver=fake.resolve,
            requester=fake.request,
        )


@pytest.mark.asyncio
async def test_not_found_rate_limit_unavailable_and_malformed_json_are_distinct() -> None:
    dns = {"social.example": ("93.184.216.34",)}

    not_found = FakeTransport(dns=dns, responses=[response(404)])
    assert (
        await fetch_webfinger_jrd(
            "https://social.example/@alice",
            resolver=not_found.resolve,
            requester=not_found.request,
        )
        is None
    )

    limited = FakeTransport(
        dns=dns,
        responses=[response(429, headers={"retry-after": "12"})],
    )
    with pytest.raises(ProviderRemoteRateLimitError) as limited_error:
        await fetch_webfinger_jrd(
            "https://social.example/@alice",
            resolver=limited.resolve,
            requester=limited.request,
        )
    assert limited_error.value.retry_after == 12.0

    unavailable = FakeTransport(dns=dns, responses=[response(503)])
    with pytest.raises(ProviderTransientError):
        await fetch_webfinger_jrd(
            "https://social.example/@alice",
            resolver=unavailable.resolve,
            requester=unavailable.request,
        )

    malformed = FakeTransport(
        dns=dns,
        responses=[response(200, body=b"not-json", headers={"content-type": "application/jrd+json"})],
    )
    with pytest.raises(ProviderResultValidationError, match="invalid JSON"):
        await fetch_webfinger_jrd(
            "https://social.example/@alice",
            resolver=malformed.resolve,
            requester=malformed.request,
        )


@pytest.mark.asyncio
async def test_redirect_count_is_bounded() -> None:
    fake = FakeTransport(
        dns={
            "social.example": ("93.184.216.34",),
            "wf.example": ("142.250.72.14",),
        },
        responses=[
            response(307, headers={"location": "https://wf.example/one?resource=x"}),
            response(307, headers={"location": "https://social.example/two?resource=x"}),
            response(307, headers={"location": "https://wf.example/three?resource=x"}),
            response(307, headers={"location": "https://social.example/four?resource=x"}),
        ],
    )

    with pytest.raises(ProviderResultValidationError, match="redirect limit"):
        await fetch_webfinger_jrd(
            "https://social.example/@alice",
            resolver=fake.resolve,
            requester=fake.request,
        )

    assert len(fake.requests) == 4
