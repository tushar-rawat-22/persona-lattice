# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
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


_API_ENDPOINT = "https://www.wikidata.org/w/api.php"
_USER_AGENT = "PersonaLattice/0.0.1 (https://github.com/tushar-rawat-22/persona-lattice; wikidata-exact-entity-research)"
_MAX_RAW_RESPONSE_BYTES = 32 * 1024
_QID_RE = re.compile(r"^Q[1-9][0-9]*$")
_MAX_LABEL_LENGTH = 256
_MAX_DESCRIPTION_LENGTH = 512

WikidataFetch = Callable[[str], Awaitable[dict[str, object] | None]]


def wikidata_entity_id_from_url(value: str) -> str | None:
    """Return the exact QID from a canonical Wikidata item URL."""

    try:
        parts = urlsplit(value)
        port = parts.port
    except ValueError:
        return None
    if (
        parts.scheme != "https"
        or parts.hostname is None
        or parts.hostname.casefold() != "www.wikidata.org"
        or parts.username is not None
        or parts.password is not None
        or port is not None
        or parts.query
        or parts.fragment
    ):
        return None

    path = parts.path[:-1] if parts.path.endswith("/") and parts.path != "/" else parts.path
    prefix = "/wiki/"
    if not path.startswith(prefix):
        return None
    entity_id = path[len(prefix) :]
    if _QID_RE.fullmatch(entity_id) is None:
        return None
    return entity_id


def _retry_after(exc: HTTPError) -> float | None:
    raw = exc.headers.get("Retry-After") if exc.headers is not None else None
    if raw is None:
        return None
    try:
        value = float(raw)
    except ValueError:
        return None
    return value if value >= 0 else None


def _fetch_wikidata_entity_sync(entity_id: str) -> dict[str, object] | None:
    request_url = f"{_API_ENDPOINT}?{urlencode({'action': 'wbgetentities', 'ids': entity_id, 'props': 'labels|descriptions', 'languages': 'en', 'format': 'json', 'formatversion': '2'})}"
    request = Request(
        request_url,
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
            raise ProviderTransientError("Wikidata entity API was unavailable.") from exc
        raise ProviderExecutionError("Wikidata entity API rejected the request.") from exc
    except (URLError, TimeoutError) as exc:
        raise ProviderTransientError("Wikidata entity API was unavailable.") from exc

    if len(raw) > _MAX_RAW_RESPONSE_BYTES:
        raise ProviderResponseTooLarge("Wikidata entity API response exceeded the adapter limit.")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProviderResultValidationError("Wikidata entity API returned invalid JSON.") from exc
    if not isinstance(payload, dict):
        raise ProviderResultValidationError("Wikidata entity API returned an invalid response shape.")
    return payload


async def fetch_wikidata_entity(entity_id: str) -> dict[str, object] | None:
    return await asyncio.to_thread(_fetch_wikidata_entity_sync, entity_id)


def _language_value(entity: dict[str, object], field: str, *, maximum: int) -> str | None:
    values = entity.get(field)
    if values is None:
        return None
    if not isinstance(values, dict):
        raise ProviderResultValidationError(f"Wikidata entity has invalid {field}.")
    english = values.get("en")
    if english is None:
        return None
    if not isinstance(english, dict):
        raise ProviderResultValidationError(f"Wikidata entity has invalid English {field}.")
    value = english.get("value")
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ProviderResultValidationError(f"Wikidata entity has invalid English {field} value.")
    return value


def _entity_from_payload(payload: dict[str, object], *, expected_entity_id: str) -> dict[str, object] | None:
    entities = payload.get("entities")
    if not isinstance(entities, dict):
        raise ProviderResultValidationError("Wikidata response is missing entities.")
    entity = entities.get(expected_entity_id)
    if entity is None:
        return None
    if not isinstance(entity, dict):
        raise ProviderResultValidationError("Wikidata returned an invalid entity shape.")
    if entity.get("missing") is not None:
        return None
    returned_id = entity.get("id")
    if returned_id != expected_entity_id:
        raise ProviderResultValidationError("Wikidata returned a different entity id.")
    entity_type = entity.get("type")
    if entity_type != "item":
        raise ProviderResultValidationError("Wikidata returned a non-item entity.")

    label = _language_value(entity, "labels", maximum=_MAX_LABEL_LENGTH)
    description = _language_value(entity, "descriptions", maximum=_MAX_DESCRIPTION_LENGTH)
    if label is None and description is None:
        return None

    details: dict[str, object] = {
        "wikidata_entity_id": expected_entity_id,
        "data_license": "CC0",
        "api_attribution": "Wikidata",
        "identity_claim": False,
    }
    if label is not None:
        details["wikidata_label_en"] = label
    if description is not None:
        details["wikidata_description_en"] = description
    return details


class WikidataExactEntityProvider:
    descriptor = PROVIDER_BY_NAME["wikidata_exact_entity"]

    def __init__(self, *, fetcher: WikidataFetch = fetch_wikidata_entity) -> None:
        self.fetcher = fetcher

    async def execute(self, query: ProviderQuery, secret: str | None) -> ProviderResult:
        if secret is not None:
            raise ProviderValidationError("Wikidata exact-entity lookup does not accept credentials.")
        if query.identifier_kind != "url":
            raise ProviderValidationError("Wikidata exact-entity lookup only accepts URLs.")

        entity_id = wikidata_entity_id_from_url(query.identifier_value)
        if entity_id is None:
            raise ProviderValidationError("Wikidata exact-entity lookup requires an exact item URL.")

        payload = await self.fetcher(entity_id)
        if payload is None:
            return ProviderResult(observations=())
        details = _entity_from_payload(payload, expected_entity_id=entity_id)
        if details is None:
            return ProviderResult(observations=())
        return ProviderResult(
            observations=(
                ProviderObservationData(
                    source_locator=f"https://www.wikidata.org/wiki/{entity_id}",
                    payload=details,
                ),
            )
        )
