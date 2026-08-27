# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import datetime
import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
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


_API_BASE = "https://api.gleif.org/api/v1/lei-records"
_USER_AGENT = (
    "PersonaLattice/0.0.1 "
    "(https://github.com/tushar-rawat-22/persona-lattice; gleif-exact-lei-research)"
)
_MAX_RAW_RESPONSE_BYTES = 128 * 1024
_MAX_LEGAL_NAME_LENGTH = 500
_MAX_STATUS_LENGTH = 40
_MAX_JURISDICTION_LENGTH = 32
_LEI_RE = re.compile(r"^[A-Z0-9]{18}[0-9]{2}$")

GleifFetch = Callable[[str], Awaitable[dict[str, object] | None]]


def _valid_lei_checksum(value: str) -> bool:
    """Return whether a syntactically valid LEI satisfies ISO 7064 MOD 97-10."""

    if _LEI_RE.fullmatch(value) is None:
        return False
    remainder = 0
    for character in value:
        digits = character if character.isdigit() else str(ord(character) - ord("A") + 10)
        for digit in digits:
            remainder = (remainder * 10 + int(digit)) % 97
    return remainder == 1


def gleif_lei_from_url(value: str) -> str | None:
    """Return the LEI from an exact canonical GLEIF public record URL."""

    try:
        parts = urlsplit(value)
        port = parts.port
    except ValueError:
        return None
    if (
        parts.scheme != "https"
        or parts.hostname is None
        or parts.hostname.casefold() != "search.gleif.org"
        or parts.username is not None
        or parts.password is not None
        or port is not None
        or parts.query
        or parts.path != "/"
    ):
        return None
    prefix = "/record/"
    if not parts.fragment.startswith(prefix) or parts.fragment.count("/") != 2:
        return None
    lei = parts.fragment[len(prefix) :]
    if not _valid_lei_checksum(lei):
        return None
    return lei


def _retry_after(exc: HTTPError) -> float | None:
    raw = exc.headers.get("Retry-After") if exc.headers is not None else None
    if raw is None:
        return None
    try:
        value = float(raw)
    except ValueError:
        return None
    return value if value >= 0 else None


def _fetch_gleif_lei_sync(lei: str) -> dict[str, object] | None:
    query = urlencode({"page[size]": "1", "filter[lei]": lei})
    request = Request(
        f"{_API_BASE}?{query}",
        headers={
            "Accept": "application/vnd.api+json, application/json",
            "User-Agent": _USER_AGENT,
        },
        method="GET",
    )
    try:
        with urlopen(request, timeout=4.0) as response:
            raw = response.read(_MAX_RAW_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        if exc.code == 429:
            raise ProviderRemoteRateLimitError(retry_after=_retry_after(exc)) from exc
        if exc.code in {408, 500, 502, 503, 504}:
            raise ProviderTransientError("GLEIF LEI API was unavailable.") from exc
        raise ProviderExecutionError("GLEIF LEI API rejected the request.") from exc
    except (URLError, TimeoutError) as exc:
        raise ProviderTransientError("GLEIF LEI API was unavailable.") from exc

    if len(raw) > _MAX_RAW_RESPONSE_BYTES:
        raise ProviderResponseTooLarge("GLEIF LEI API response exceeded the adapter limit.")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProviderResultValidationError("GLEIF LEI API returned invalid JSON.") from exc
    if not isinstance(payload, dict):
        raise ProviderResultValidationError("GLEIF LEI API returned an invalid response shape.")

    records = payload.get("data")
    if not isinstance(records, list):
        raise ProviderResultValidationError("GLEIF LEI API response is missing its data list.")
    if not records:
        return None
    if len(records) != 1 or not isinstance(records[0], dict):
        raise ProviderResultValidationError("GLEIF exact LEI lookup returned an ambiguous record set.")
    return records[0]


async def fetch_gleif_lei(lei: str) -> dict[str, object] | None:
    return await asyncio.to_thread(_fetch_gleif_lei_sync, lei)


def _bounded_text(value: object, *, field: str, maximum: int) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ProviderResultValidationError(f"GLEIF record contains an invalid {field}.")
    return value


def _optional_timestamp(value: object, *, field: str) -> str | None:
    if value is None:
        return None
    text = _bounded_text(value, field=field, maximum=64)
    try:
        datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ProviderResultValidationError(f"GLEIF record contains an invalid {field}.") from exc
    return text


def _details_from_record(record: dict[str, object], *, expected_lei: str) -> dict[str, object]:
    record_type = record.get("type")
    if record_type != "lei-records":
        raise ProviderResultValidationError("GLEIF returned an unexpected record type.")
    record_id = record.get("id")
    if record_id != expected_lei:
        raise ProviderResultValidationError("GLEIF returned a different LEI record id.")

    attributes = record.get("attributes")
    if not isinstance(attributes, dict):
        raise ProviderResultValidationError("GLEIF record is missing attributes.")
    if attributes.get("lei") != expected_lei:
        raise ProviderResultValidationError("GLEIF returned a different LEI in record attributes.")

    entity = attributes.get("entity")
    registration = attributes.get("registration")
    if not isinstance(entity, dict) or not isinstance(registration, dict):
        raise ProviderResultValidationError("GLEIF record is missing entity or registration metadata.")

    legal_name = entity.get("legalName")
    if not isinstance(legal_name, dict):
        raise ProviderResultValidationError("GLEIF record is missing the legal name object.")

    details: dict[str, object] = {
        "gleif_lei": expected_lei,
        "gleif_legal_name": _bounded_text(
            legal_name.get("name"),
            field="legal name",
            maximum=_MAX_LEGAL_NAME_LENGTH,
        ),
        "entity_status": _bounded_text(
            entity.get("status"),
            field="entity status",
            maximum=_MAX_STATUS_LENGTH,
        ),
        "registration_status": _bounded_text(
            registration.get("status"),
            field="registration status",
            maximum=_MAX_STATUS_LENGTH,
        ),
        "data_license": "CC0",
        "api_attribution": "Global Legal Entity Identifier Foundation (GLEIF)",
        "identity_claim": False,
    }

    jurisdiction = entity.get("jurisdiction")
    if jurisdiction is not None:
        details["legal_jurisdiction"] = _bounded_text(
            jurisdiction,
            field="legal jurisdiction",
            maximum=_MAX_JURISDICTION_LENGTH,
        )

    last_update = _optional_timestamp(registration.get("lastUpdateDate"), field="last update date")
    if last_update is not None:
        details["last_update_date"] = last_update
    return details


class GleifExactLeiProvider:
    descriptor = PROVIDER_BY_NAME["gleif_exact_lei"]

    def __init__(self, *, fetcher: GleifFetch = fetch_gleif_lei) -> None:
        self.fetcher = fetcher

    async def execute(self, query: ProviderQuery, secret: str | None) -> ProviderResult:
        if secret is not None:
            raise ProviderValidationError("GLEIF exact-LEI lookup does not accept credentials.")
        if query.identifier_kind != "url":
            raise ProviderValidationError("GLEIF exact-LEI lookup only accepts URLs.")

        lei = gleif_lei_from_url(query.identifier_value)
        if lei is None:
            raise ProviderValidationError("GLEIF exact-LEI lookup requires a canonical GLEIF record URL.")

        record = await self.fetcher(lei)
        if record is None:
            return ProviderResult(observations=())
        details = _details_from_record(record, expected_lei=lei)
        return ProviderResult(
            observations=(
                ProviderObservationData(
                    source_locator=f"https://search.gleif.org/#/record/{lei}",
                    payload=details,
                ),
            )
        )
