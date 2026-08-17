# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from .base import ProviderObservationData, ProviderQuery, ProviderResult
from .errors import (
    ProviderExecutionError,
    ProviderRemoteRateLimitError,
    ProviderTransientError,
    ProviderValidationError,
)
from .registry import PROVIDER_BY_NAME


_MAX_RAW_RESPONSE_BYTES = 64 * 1024
_ALLOWED_PUBLIC_FIELDS = (
    "handle",
    "email",
    "vkId",
    "openId",
    "firstName",
    "lastName",
    "country",
    "city",
    "organization",
    "contribution",
    "rank",
    "rating",
    "maxRank",
    "maxRating",
    "lastOnlineTimeSeconds",
    "registrationTimeSeconds",
    "friendOfCount",
    "avatar",
    "titlePhoto",
)

CodeforcesFetch = Callable[[str], Awaitable[dict[str, object] | None]]


def _fetch_codeforces_public_profile_sync(handle: str) -> dict[str, object] | None:
    query = urlencode({"handles": handle, "checkHistoricHandles": "true"})
    request = Request(
        f"https://codeforces.com/api/user.info?{query}",
        headers={
            "Accept": "application/json",
            "User-Agent": "PersonaLattice/0.0.1 public-profile-research",
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
            raise ProviderRemoteRateLimitError(retry_after=2.0) from exc
        if exc.code in {408, 500, 502, 503, 504}:
            raise ProviderTransientError("Codeforces public profile endpoint was unavailable.") from exc
        raise ProviderExecutionError("Codeforces public profile request failed.") from exc
    except (URLError, TimeoutError) as exc:
        raise ProviderTransientError("Codeforces public profile request failed.") from exc

    if len(raw) > _MAX_RAW_RESPONSE_BYTES:
        raise ProviderValidationError("Codeforces public profile response exceeded the adapter limit.")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProviderValidationError("Codeforces public profile returned invalid JSON.") from exc
    if not isinstance(payload, dict):
        raise ProviderValidationError("Codeforces public profile returned an invalid response shape.")

    status = payload.get("status")
    if status == "FAILED":
        comment = payload.get("comment")
        if isinstance(comment, str):
            folded = comment.casefold()
            if "not found" in folded:
                return None
            if "call limit exceeded" in folded:
                raise ProviderRemoteRateLimitError(retry_after=2.0)
        raise ProviderExecutionError("Codeforces public profile lookup failed.")
    if status != "OK":
        raise ProviderValidationError("Codeforces public profile returned an invalid status.")

    result = payload.get("result")
    if not isinstance(result, list):
        raise ProviderValidationError("Codeforces public profile returned an invalid result shape.")
    if not result:
        return None
    if len(result) != 1 or not isinstance(result[0], dict):
        raise ProviderValidationError("Codeforces public profile returned an invalid user result.")
    return result[0]


async def fetch_codeforces_public_profile(handle: str) -> dict[str, object] | None:
    return await asyncio.to_thread(_fetch_codeforces_public_profile_sync, handle)


class CodeforcesPublicProfileProvider:
    descriptor = PROVIDER_BY_NAME["codeforces_public_api"]

    def __init__(self, *, fetcher: CodeforcesFetch = fetch_codeforces_public_profile) -> None:
        self.fetcher = fetcher

    async def execute(self, query: ProviderQuery, secret: str | None) -> ProviderResult:
        if secret is not None:
            raise ProviderValidationError("Codeforces public profile lookup does not accept credentials.")
        if query.identifier_kind != "username":
            raise ProviderValidationError("Codeforces public profile lookup accepts usernames only.")

        payload = await self.fetcher(query.identifier_value)
        if payload is None:
            return ProviderResult(observations=())

        returned_handle = payload.get("handle")
        if not isinstance(returned_handle, str) or not returned_handle.strip():
            raise ProviderValidationError("Codeforces public profile is missing handle.")

        details = {field: payload.get(field) for field in _ALLOWED_PUBLIC_FIELDS}
        details.update(
            {
                "account_candidate": True,
                "identity_claim": False,
                "field_visibility": "public_profile_api",
                "matched_by": (
                    "exact_handle"
                    if returned_handle.casefold() == query.identifier_value.casefold()
                    else "historic_handle"
                ),
            }
        )
        source_locator = f"https://codeforces.com/profile/{quote(returned_handle, safe='')}"
        return ProviderResult(
            observations=(
                ProviderObservationData(source_locator=source_locator, payload=details),
            )
        )
