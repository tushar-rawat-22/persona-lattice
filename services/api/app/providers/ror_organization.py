# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import json
import re
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


_API_BASE = "https://api.ror.org/v2/organizations"
_USER_AGENT = (
    "PersonaLattice/0.0.1 "
    "(https://github.com/tushar-rawat-22/persona-lattice; ror-exact-organization-research)"
)
_MAX_RAW_RESPONSE_BYTES = 32 * 1024
_MAX_NAME_LENGTH = 256
_MAX_TYPES = 8
_MAX_TYPE_LENGTH = 32
_ROR_ID_RE = re.compile(r"^0[a-hj-km-np-tv-z0-9]{6}[0-9]{2}$")

RorFetch = Callable[[str], Awaitable[dict[str, object] | None]]


def ror_id_from_url(value: str) -> str | None:
    """Return the unique ROR ID from an exact canonical ROR URL."""

    try:
        parts = urlsplit(value)
        port = parts.port
    except ValueError:
        return None
    if (
        parts.scheme != "https"
        or parts.hostname is None
        or parts.hostname.casefold() != "ror.org"
        or parts.username is not None
        or parts.password is not None
        or port is not None
        or parts.query
        or parts.fragment
    ):
        return None
    if parts.path.count("/") != 1 or not parts.path.startswith("/"):
        return None
    ror_id = parts.path[1:]
    if _ROR_ID_RE.fullmatch(ror_id) is None:
        return None
    return ror_id


def _retry_after(exc: HTTPError) -> float | None:
    raw = exc.headers.get("Retry-After") if exc.headers is not None else None
    if raw is None:
        return None
    try:
        value = float(raw)
    except ValueError:
        return None
    return value if value >= 0 else None


def _fetch_ror_organization_sync(ror_id: str) -> dict[str, object] | None:
    request = Request(
        f"{_API_BASE}/{quote(ror_id, safe='')}",
        headers={
            "Accept": "application/json",
            "User-Agent": _USER_AGENT,
        },
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
            raise ProviderTransientError("ROR organization API was unavailable.") from exc
        raise ProviderExecutionError("ROR organization API rejected the request.") from exc
    except (URLError, TimeoutError) as exc:
        raise ProviderTransientError("ROR organization API was unavailable.") from exc

    if len(raw) > _MAX_RAW_RESPONSE_BYTES:
        raise ProviderResponseTooLarge("ROR organization API response exceeded the adapter limit.")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProviderResultValidationError("ROR organization API returned invalid JSON.") from exc
    if not isinstance(payload, dict):
        raise ProviderResultValidationError("ROR organization API returned an invalid response shape.")
    return payload


async def fetch_ror_organization(ror_id: str) -> dict[str, object] | None:
    return await asyncio.to_thread(_fetch_ror_organization_sync, ror_id)


def _display_name(payload: dict[str, object]) -> str:
    names = payload.get("names")
    if not isinstance(names, list) or not names:
        raise ProviderResultValidationError("ROR record is missing names.")
    matches: list[str] = []
    for item in names:
        if not isinstance(item, dict):
            raise ProviderResultValidationError("ROR record contains an invalid name entry.")
        types = item.get("types")
        if not isinstance(types, list) or not all(isinstance(value, str) for value in types):
            raise ProviderResultValidationError("ROR record contains invalid name types.")
        if "ror_display" not in types:
            continue
        value = item.get("value")
        if not isinstance(value, str) or not value.strip() or len(value) > _MAX_NAME_LENGTH:
            raise ProviderResultValidationError("ROR record contains an invalid display name.")
        matches.append(value)
    if len(matches) != 1:
        raise ProviderResultValidationError("ROR record must contain exactly one display name.")
    return matches[0]


def _organization_types(payload: dict[str, object]) -> list[str]:
    raw_types = payload.get("types")
    if raw_types is None:
        return []
    if not isinstance(raw_types, list) or len(raw_types) > _MAX_TYPES:
        raise ProviderResultValidationError("ROR record contains invalid organization types.")
    values: list[str] = []
    for value in raw_types:
        if not isinstance(value, str) or not value.strip() or len(value) > _MAX_TYPE_LENGTH:
            raise ProviderResultValidationError("ROR record contains invalid organization types.")
        values.append(value)
    if len(values) != len(set(values)):
        raise ProviderResultValidationError("ROR record contains duplicate organization types.")
    return values


def _details_from_payload(payload: dict[str, object], *, expected_ror_id: str) -> dict[str, object]:
    canonical_id = f"https://ror.org/{expected_ror_id}"
    returned_id = payload.get("id")
    if returned_id != canonical_id:
        raise ProviderResultValidationError("ROR returned a different organization id.")
    status = payload.get("status")
    if status != "active":
        raise ProviderResultValidationError("ROR returned a non-active organization record.")

    details: dict[str, object] = {
        "ror_id": canonical_id,
        "ror_display_name": _display_name(payload),
        "record_status": status,
        "data_license": "CC0",
        "api_attribution": "Research Organization Registry (ROR)",
        "identity_claim": False,
    }
    organization_types = _organization_types(payload)
    if organization_types:
        details["organization_types"] = organization_types
    return details


class RorExactOrganizationProvider:
    descriptor = PROVIDER_BY_NAME["ror_exact_organization"]

    def __init__(self, *, fetcher: RorFetch = fetch_ror_organization) -> None:
        self.fetcher = fetcher

    async def execute(self, query: ProviderQuery, secret: str | None) -> ProviderResult:
        if secret is not None:
            raise ProviderValidationError("ROR exact-organization lookup does not accept credentials.")
        if query.identifier_kind != "url":
            raise ProviderValidationError("ROR exact-organization lookup only accepts URLs.")

        ror_id = ror_id_from_url(query.identifier_value)
        if ror_id is None:
            raise ProviderValidationError("ROR exact-organization lookup requires a canonical ROR URL.")

        payload = await self.fetcher(ror_id)
        if payload is None:
            return ProviderResult(observations=())
        details = _details_from_payload(payload, expected_ror_id=ror_id)
        return ProviderResult(
            observations=(
                ProviderObservationData(
                    source_locator=f"https://ror.org/{ror_id}",
                    payload=details,
                ),
            )
        )
