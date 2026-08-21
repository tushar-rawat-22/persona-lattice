# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
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


_SPARQL_ENDPOINT = "https://sparql.dblp.org/sparql"
_USER_AGENT = (
    "PersonaLattice/0.0.1 "
    "(https://github.com/tushar-rawat-22/persona-lattice; dblp-exact-person-research)"
)
_MAX_RAW_RESPONSE_BYTES = 32 * 1024
_MAX_PID_LENGTH = 128
_MAX_NAME_LENGTH = 256
_PID_RE = re.compile(r"^[A-Za-z0-9-]+(?:/[A-Za-z0-9-]+)+$")

DblpFetch = Callable[[str], Awaitable[dict[str, object] | None]]


def dblp_person_pid_from_url(value: str) -> str | None:
    """Return the case-sensitive PID from an exact canonical DBLP person URL."""

    try:
        parts = urlsplit(value)
        port = parts.port
    except ValueError:
        return None
    if (
        parts.scheme != "https"
        or parts.hostname is None
        or parts.hostname.casefold() != "dblp.org"
        or parts.username is not None
        or parts.password is not None
        or port is not None
        or parts.query
        or parts.fragment
        or not parts.path.startswith("/pid/")
    ):
        return None
    pid = parts.path.removeprefix("/pid/")
    if not pid or len(pid) > _MAX_PID_LENGTH or _PID_RE.fullmatch(pid) is None:
        return None
    return pid


def _retry_after(exc: HTTPError) -> float | None:
    raw = exc.headers.get("Retry-After") if exc.headers is not None else None
    if raw is None:
        return None
    try:
        value = float(raw)
    except ValueError:
        return None
    return value if value >= 0 else None


def _canonical_person_url(pid: str) -> str:
    return f"https://dblp.org/pid/{pid}"


def _sparql_query(pid: str) -> str:
    person = _canonical_person_url(pid)
    return (
        "PREFIX dblp: <https://dblp.org/rdf/schema#>\n"
        "SELECT ?person ?name WHERE {\n"
        f"  VALUES ?person {{ <{person}> }}\n"
        "  ?person a dblp:Person ;\n"
        "          dblp:primaryCreatorName ?name .\n"
        "}\n"
        "LIMIT 2\n"
    )


def _fetch_dblp_person_sync(pid: str) -> dict[str, object] | None:
    request = Request(
        _SPARQL_ENDPOINT,
        data=_sparql_query(pid).encode("utf-8"),
        headers={
            "Accept": "application/sparql-results+json",
            "Content-Type": "application/sparql-query; charset=utf-8",
            "User-Agent": _USER_AGENT,
        },
        method="POST",
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
            raise ProviderTransientError("DBLP SPARQL service was unavailable.") from exc
        raise ProviderExecutionError("DBLP SPARQL service rejected the request.") from exc
    except (URLError, TimeoutError) as exc:
        raise ProviderTransientError("DBLP SPARQL service was unavailable.") from exc

    if len(raw) > _MAX_RAW_RESPONSE_BYTES:
        raise ProviderResponseTooLarge("DBLP SPARQL response exceeded the adapter limit.")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProviderResultValidationError("DBLP SPARQL service returned invalid JSON.") from exc
    if not isinstance(payload, dict):
        raise ProviderResultValidationError("DBLP SPARQL service returned an invalid response shape.")
    return payload


async def fetch_dblp_person(pid: str) -> dict[str, object] | None:
    return await asyncio.to_thread(_fetch_dblp_person_sync, pid)


def _details_from_payload(
    payload: dict[str, object],
    *,
    expected_pid: str,
) -> dict[str, object] | None:
    results = payload.get("results")
    if not isinstance(results, dict):
        raise ProviderResultValidationError("DBLP SPARQL result is missing results.")
    bindings = results.get("bindings")
    if not isinstance(bindings, list) or len(bindings) > 2:
        raise ProviderResultValidationError("DBLP SPARQL result contains invalid bindings.")
    if not bindings:
        return None
    if len(bindings) != 1:
        raise ProviderResultValidationError("DBLP person result is not uniquely identified.")

    row = bindings[0]
    if not isinstance(row, dict):
        raise ProviderResultValidationError("DBLP SPARQL result contains an invalid row.")
    person = row.get("person")
    name = row.get("name")
    if not isinstance(person, dict) or not isinstance(name, dict):
        raise ProviderResultValidationError("DBLP person result is missing required bindings.")

    canonical_url = _canonical_person_url(expected_pid)
    if person.get("type") != "uri" or person.get("value") != canonical_url:
        raise ProviderResultValidationError("DBLP returned a different person resource.")
    value = name.get("value")
    if (
        name.get("type") not in {"literal", "typed-literal"}
        or not isinstance(value, str)
        or not value.strip()
        or value != value.strip()
        or len(value) > _MAX_NAME_LENGTH
    ):
        raise ProviderResultValidationError("DBLP returned an invalid primary creator name.")

    return {
        "dblp_pid": canonical_url,
        "dblp_primary_name": value,
        "data_license": "CC0",
        "api_attribution": "dblp computer science bibliography",
        "identity_claim": False,
    }


class DblpExactPersonProvider:
    descriptor = PROVIDER_BY_NAME["dblp_exact_person"]

    def __init__(self, *, fetcher: DblpFetch = fetch_dblp_person) -> None:
        self.fetcher = fetcher

    async def execute(self, query: ProviderQuery, secret: str | None) -> ProviderResult:
        if secret is not None:
            raise ProviderValidationError("DBLP exact-person lookup does not accept credentials.")
        if query.identifier_kind != "url":
            raise ProviderValidationError("DBLP exact-person lookup only accepts URLs.")

        pid = dblp_person_pid_from_url(query.identifier_value)
        if pid is None:
            raise ProviderValidationError("DBLP exact-person lookup requires a canonical DBLP PID URL.")

        payload = await self.fetcher(pid)
        if payload is None:
            return ProviderResult(observations=())
        details = _details_from_payload(payload, expected_pid=pid)
        if details is None:
            return ProviderResult(observations=())
        return ProviderResult(
            observations=(
                ProviderObservationData(
                    source_locator=_canonical_person_url(pid),
                    payload=details,
                ),
            )
        )
