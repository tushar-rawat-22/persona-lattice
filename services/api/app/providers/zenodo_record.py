# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen

from .base import ProviderObservationData, ProviderQuery, ProviderResult
from .errors import (
    ProviderExecutionError,
    ProviderRemoteRateLimitError,
    ProviderResponseTooLarge,
    ProviderResultValidationError,
    ProviderTransientError,
    ProviderValidationError,
)
from .registry import PROVIDER_BY_NAME


_API_BASE = "https://zenodo.org/api/records"
_USER_AGENT = (
    "PersonaLattice/0.0.1 "
    "(https://github.com/tushar-rawat-22/persona-lattice; zenodo-exact-record-research)"
)
_MAX_RAW_RESPONSE_BYTES = 32 * 1024
_MAX_TITLE_LENGTH = 512

ZenodoFetch = Callable[[str], Awaitable[dict[str, object] | None]]


def zenodo_record_id_from_url(value: str) -> str | None:
    """Return the record ID from an exact canonical Zenodo record URL."""

    try:
        parts = urlsplit(value)
        port = parts.port
    except ValueError:
        return None
    if (
        parts.scheme != "https"
        or parts.hostname is None
        or parts.hostname.casefold() != "zenodo.org"
        or parts.username is not None
        or parts.password is not None
        or port is not None
        or parts.query
        or parts.fragment
    ):
        return None
    segments = parts.path.split("/")
    if len(segments) != 3 or segments[0] or segments[1] != "records":
        return None
    record_id = segments[2]
    if not record_id.isascii() or not record_id.isdecimal() or record_id.startswith("0"):
        return None
    return record_id


def _retry_after(exc: HTTPError) -> float | None:
    raw = exc.headers.get("Retry-After") if exc.headers is not None else None
    if raw is None:
        return None
    try:
        value = float(raw)
    except ValueError:
        return None
    return value if value >= 0 else None


def _fetch_zenodo_record_sync(record_id: str) -> dict[str, object] | None:
    request = Request(
        f"{_API_BASE}/{quote(record_id, safe='')}",
        headers={"Accept": "application/json", "User-Agent": _USER_AGENT},
        method="GET",
    )
    try:
        with urlopen(request, timeout=4.0) as response:
            raw = response.read(_MAX_RAW_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        if exc.code == 404:
            return None
        if exc.code == 429:
            raise ProviderRemoteRateLimitError(retry_after=_retry_after(exc)) from exc
        if exc.code in {408, 500, 502, 503, 504}:
            raise ProviderTransientError("Zenodo records API was unavailable.") from exc
        raise ProviderExecutionError("Zenodo records API rejected the request.") from exc
    except (URLError, TimeoutError) as exc:
        raise ProviderTransientError("Zenodo records API was unavailable.") from exc

    if len(raw) > _MAX_RAW_RESPONSE_BYTES:
        raise ProviderResponseTooLarge("Zenodo record response exceeded the adapter limit.")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProviderResultValidationError("Zenodo records API returned invalid JSON.") from exc
    if not isinstance(payload, dict):
        raise ProviderResultValidationError("Zenodo records API returned an invalid response shape.")
    return payload


async def fetch_zenodo_record(record_id: str) -> dict[str, object] | None:
    return await asyncio.to_thread(_fetch_zenodo_record_sync, record_id)


def _record_id(payload: dict[str, object]) -> str:
    value = payload.get("id")
    if isinstance(value, int) and not isinstance(value, bool) and value > 0:
        return str(value)
    if isinstance(value, str) and value.isascii() and value.isdecimal() and not value.startswith("0"):
        return value
    raise ProviderResultValidationError("Zenodo record is missing a valid record id.")


def _details_from_payload(payload: dict[str, object], *, expected_record_id: str) -> dict[str, object]:
    returned_id = _record_id(payload)
    if returned_id != expected_record_id:
        raise ProviderResultValidationError("Zenodo returned a different record id.")
    metadata = payload.get("metadata")
    if not isinstance(metadata, dict):
        raise ProviderResultValidationError("Zenodo record is missing metadata.")
    title = metadata.get("title")
    if not isinstance(title, str) or not title.strip() or len(title) > _MAX_TITLE_LENGTH:
        raise ProviderResultValidationError("Zenodo record contains an invalid title.")
    return {
        "zenodo_record_id": expected_record_id,
        "zenodo_record_title": title,
        "data_license": "CC0",
        "api_attribution": "Zenodo (CERN)",
        "identity_claim": False,
    }


class ZenodoExactRecordProvider:
    descriptor = PROVIDER_BY_NAME["zenodo_exact_record"]

    def __init__(self, *, fetcher: ZenodoFetch = fetch_zenodo_record) -> None:
        self.fetcher = fetcher

    async def execute(self, query: ProviderQuery, secret: str | None) -> ProviderResult:
        if secret is not None:
            raise ProviderValidationError("Zenodo exact-record lookup does not accept credentials.")
        if query.identifier_kind != "url":
            raise ProviderValidationError("Zenodo exact-record lookup only accepts URLs.")
        record_id = zenodo_record_id_from_url(query.identifier_value)
        if record_id is None:
            raise ProviderValidationError("Zenodo exact-record lookup requires a canonical record URL.")
        payload = await self.fetcher(record_id)
        if payload is None:
            return ProviderResult(observations=())
        return ProviderResult(
            observations=(
                ProviderObservationData(
                    source_locator=f"https://zenodo.org/records/{record_id}",
                    payload=_details_from_payload(payload, expected_record_id=record_id),
                ),
            )
        )
