# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import asyncio
import base64
from collections.abc import Awaitable, Callable
from datetime import date
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


_API_BASE = "https://api.company-information.service.gov.uk/company"
_PUBLIC_BASE = "https://find-and-update.company-information.service.gov.uk/company"
_USER_AGENT = (
    "PersonaLattice/0.0.1 "
    "(https://github.com/tushar-rawat-22/persona-lattice; companies-house-exact-company-research)"
)
_MAX_RAW_RESPONSE_BYTES = 32 * 1024
_MAX_NAME_LENGTH = 256
_MAX_ENUM_LENGTH = 64
_COMPANY_NUMBER_RE = re.compile(r"^[A-Z0-9]{8}$")

CompaniesHouseFetch = Callable[[str, str], Awaitable[dict[str, object] | None]]


def companies_house_number_from_url(value: str) -> str | None:
    """Return the company number from an exact canonical Companies House company URL."""

    try:
        parts = urlsplit(value)
        port = parts.port
    except ValueError:
        return None
    if (
        parts.scheme != "https"
        or parts.hostname is None
        or parts.hostname.casefold() != "find-and-update.company-information.service.gov.uk"
        or parts.username is not None
        or parts.password is not None
        or port is not None
        or parts.query
        or parts.fragment
    ):
        return None
    prefix = "/company/"
    if not parts.path.startswith(prefix) or parts.path.count("/") != 2:
        return None
    number = parts.path[len(prefix) :]
    if _COMPANY_NUMBER_RE.fullmatch(number) is None:
        return None
    return number


def _retry_after(exc: HTTPError) -> float | None:
    raw = exc.headers.get("Retry-After") if exc.headers is not None else None
    if raw is None:
        return None
    try:
        value = float(raw)
    except ValueError:
        return None
    return value if value >= 0 else None


def _basic_authorization(secret: str) -> str:
    token = base64.b64encode(f"{secret}:".encode("utf-8")).decode("ascii")
    return f"Basic {token}"


def _fetch_company_sync(company_number: str, secret: str) -> dict[str, object] | None:
    request = Request(
        f"{_API_BASE}/{quote(company_number, safe='')}",
        headers={
            "Accept": "application/json",
            "Authorization": _basic_authorization(secret),
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
            raise ProviderTransientError("Companies House company API was unavailable.") from exc
        if exc.code in {401, 403}:
            raise ProviderExecutionError("Companies House rejected the configured API credential.") from exc
        raise ProviderExecutionError("Companies House company API rejected the request.") from exc
    except (URLError, TimeoutError) as exc:
        raise ProviderTransientError("Companies House company API was unavailable.") from exc

    if len(raw) > _MAX_RAW_RESPONSE_BYTES:
        raise ProviderResponseTooLarge("Companies House company API response exceeded the adapter limit.")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProviderResultValidationError("Companies House company API returned invalid JSON.") from exc
    if not isinstance(payload, dict):
        raise ProviderResultValidationError("Companies House company API returned an invalid response shape.")
    return payload


async def fetch_companies_house_company(company_number: str, secret: str) -> dict[str, object] | None:
    return await asyncio.to_thread(_fetch_company_sync, company_number, secret)


def _bounded_text(payload: dict[str, object], field: str, *, max_length: int) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip() or len(value) > max_length:
        raise ProviderResultValidationError(f"Companies House company has an invalid {field}.")
    return value


def _optional_creation_date(payload: dict[str, object]) -> str | None:
    value = payload.get("date_of_creation")
    if value is None:
        return None
    if not isinstance(value, str):
        raise ProviderResultValidationError("Companies House company has an invalid date_of_creation.")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ProviderResultValidationError(
            "Companies House company has an invalid date_of_creation."
        ) from exc
    if parsed.isoformat() != value:
        raise ProviderResultValidationError("Companies House company has an invalid date_of_creation.")
    return value


def _details_from_payload(
    payload: dict[str, object], *, expected_company_number: str
) -> dict[str, object]:
    returned_number = payload.get("company_number")
    if returned_number != expected_company_number:
        raise ProviderResultValidationError("Companies House returned a different company number.")

    details: dict[str, object] = {
        "companies_house_company_number": expected_company_number,
        "companies_house_registered_name": _bounded_text(
            payload, "company_name", max_length=_MAX_NAME_LENGTH
        ),
        "companies_house_status": _bounded_text(
            payload, "company_status", max_length=_MAX_ENUM_LENGTH
        ),
        "companies_house_type": _bounded_text(payload, "type", max_length=_MAX_ENUM_LENGTH),
        "api_attribution": "Companies House public register",
        "identity_claim": False,
    }
    creation_date = _optional_creation_date(payload)
    if creation_date is not None:
        details["companies_house_incorporation_date"] = creation_date
    return details


class CompaniesHouseExactCompanyProvider:
    descriptor = PROVIDER_BY_NAME["companies_house_exact_company"]

    def __init__(self, *, fetcher: CompaniesHouseFetch = fetch_companies_house_company) -> None:
        self.fetcher = fetcher

    async def execute(self, query: ProviderQuery, secret: str | None) -> ProviderResult:
        if secret is None or not secret.strip():
            raise ProviderValidationError(
                "Companies House exact-company lookup requires a server-side API key."
            )
        if query.identifier_kind != "url":
            raise ProviderValidationError("Companies House exact-company lookup only accepts URLs.")

        company_number = companies_house_number_from_url(query.identifier_value)
        if company_number is None:
            raise ProviderValidationError(
                "Companies House exact-company lookup requires a canonical public company URL."
            )

        payload = await self.fetcher(company_number, secret)
        if payload is None:
            return ProviderResult(observations=())
        details = _details_from_payload(payload, expected_company_number=company_number)
        return ProviderResult(
            observations=(
                ProviderObservationData(
                    source_locator=f"{_PUBLIC_BASE}/{company_number}",
                    payload=details,
                ),
            )
        )
