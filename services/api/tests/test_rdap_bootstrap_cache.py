# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

import pytest

from app.providers.rdap_bootstrap_cache import (
    IANA_RDAP_BOOTSTRAP_CACHE,
    IanaRdapBootstrapCache,
    RdapBootstrapHTTPResponse,
    RdapBootstrapUnavailableError,
    RdapBootstrapValidationError,
)


NOW = datetime(2026, 8, 19, 12, 0, tzinfo=timezone.utc)
BOOTSTRAP_BODY = b'{"services":[[["com"],["https://rdap.example/rdap/"]]]}'


def response(
    status: int = 200,
    *,
    headers: dict[str, str] | None = None,
    body: bytes = BOOTSTRAP_BODY,
) -> RdapBootstrapHTTPResponse:
    values = {"content-type": "application/json", "cache-control": "max-age=3600"}
    if headers:
        values.update(headers)
    return RdapBootstrapHTTPResponse(status=status, headers=values, body=body)


def test_module_exposes_one_process_wide_cache_owner() -> None:
    assert isinstance(IANA_RDAP_BOOTSTRAP_CACHE, IanaRdapBootstrapCache)


@pytest.mark.asyncio
async def test_fresh_bootstrap_is_reused_without_another_fetch() -> None:
    calls: list[dict[str, str]] = []

    async def fetcher(headers: dict[str, str]) -> RdapBootstrapHTTPResponse:
        calls.append(dict(headers))
        return response(headers={"etag": '"v1"'})

    cache = IanaRdapBootstrapCache(fetcher=fetcher)
    first = await cache.get_payload(now=NOW)
    second = await cache.get_payload(now=NOW + timedelta(minutes=30))

    assert first == second
    assert len(calls) == 1
    assert calls[0] == {}


@pytest.mark.asyncio
async def test_expired_bootstrap_uses_conditional_refresh_and_304() -> None:
    calls: list[dict[str, str]] = []

    async def fetcher(headers: dict[str, str]) -> RdapBootstrapHTTPResponse:
        calls.append(dict(headers))
        if len(calls) == 1:
            return response(
                headers={
                    "etag": '"v1"',
                    "last-modified": "Wed, 19 Aug 2026 10:00:00 GMT",
                    "cache-control": "max-age=60",
                }
            )
        return response(
            status=304,
            headers={"cache-control": "max-age=3600", "etag": '"v1"'},
            body=b"",
        )

    cache = IanaRdapBootstrapCache(fetcher=fetcher)
    first = await cache.get_payload(now=NOW)
    second = await cache.get_payload(now=NOW + timedelta(minutes=2))
    third = await cache.get_payload(now=NOW + timedelta(minutes=30))

    assert first == second == third
    assert calls == [
        {},
        {
            "If-None-Match": '"v1"',
            "If-Modified-Since": "Wed, 19 Aug 2026 10:00:00 GMT",
        },
    ]


@pytest.mark.asyncio
async def test_expires_uses_origin_date_for_freshness_lifetime() -> None:
    calls = 0

    async def fetcher(headers: dict[str, str]) -> RdapBootstrapHTTPResponse:
        nonlocal calls
        calls += 1
        return response(
            headers={
                "cache-control": "",
                "date": "Wed, 19 Aug 2026 10:00:00 GMT",
                "expires": "Wed, 19 Aug 2026 12:00:00 GMT",
            }
        )

    cache = IanaRdapBootstrapCache(fetcher=fetcher)
    await cache.get_payload(now=NOW)
    await cache.get_payload(now=NOW + timedelta(hours=1, minutes=59))

    assert calls == 1


@pytest.mark.asyncio
async def test_no_store_response_is_returned_but_not_cached() -> None:
    calls = 0

    async def fetcher(headers: dict[str, str]) -> RdapBootstrapHTTPResponse:
        nonlocal calls
        calls += 1
        return response(headers={"cache-control": "no-store", "etag": '"v1"'})

    cache = IanaRdapBootstrapCache(fetcher=fetcher)
    first = await cache.get_payload(now=NOW)
    second = await cache.get_payload(now=NOW)

    assert first == second
    assert calls == 2


@pytest.mark.asyncio
async def test_refresh_failure_does_not_serve_expired_authority() -> None:
    attempts = 0

    async def fetcher(headers: dict[str, str]) -> RdapBootstrapHTTPResponse:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return response(headers={"cache-control": "max-age=1"})
        raise RdapBootstrapUnavailableError("offline")

    cache = IanaRdapBootstrapCache(fetcher=fetcher)
    await cache.get_payload(now=NOW)

    with pytest.raises(RdapBootstrapUnavailableError, match="offline"):
        await cache.get_payload(now=NOW + timedelta(seconds=2))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("bad_response", "message"),
    [
        (response(body=b"[]"), "JSON object"),
        (response(body=b'{"services":[]}'), "service count"),
        (
            response(headers={"content-type": "text/plain"}),
            "unsupported media type",
        ),
        (
            response(headers={"content-type": "application/rdap+json"}),
            "unsupported media type",
        ),
        (response(status=302, headers={}), "unexpectedly redirected"),
    ],
)
async def test_malformed_bootstrap_responses_fail_closed(
    bad_response: RdapBootstrapHTTPResponse,
    message: str,
) -> None:
    async def fetcher(headers: dict[str, str]) -> RdapBootstrapHTTPResponse:
        return bad_response

    cache = IanaRdapBootstrapCache(fetcher=fetcher)
    with pytest.raises(RdapBootstrapValidationError, match=message):
        await cache.get_payload(now=NOW)


@pytest.mark.asyncio
async def test_concurrent_first_reads_share_one_refresh() -> None:
    calls = 0
    started = asyncio.Event()
    release = asyncio.Event()

    async def fetcher(headers: dict[str, str]) -> RdapBootstrapHTTPResponse:
        nonlocal calls
        calls += 1
        started.set()
        await release.wait()
        return response()

    cache = IanaRdapBootstrapCache(fetcher=fetcher)
    first_task = asyncio.create_task(cache.get_payload(now=NOW))
    await started.wait()
    second_task = asyncio.create_task(cache.get_payload(now=NOW))
    release.set()

    first, second = await asyncio.gather(first_task, second_task)
    assert first == second
    assert calls == 1


@pytest.mark.asyncio
async def test_returned_payload_cannot_mutate_cached_snapshot() -> None:
    async def fetcher(headers: dict[str, str]) -> RdapBootstrapHTTPResponse:
        return response()

    cache = IanaRdapBootstrapCache(fetcher=fetcher)
    first = await cache.get_payload(now=NOW)
    first["services"] = []

    second = await cache.get_payload(now=NOW + timedelta(minutes=5))
    assert second["services"] != []
