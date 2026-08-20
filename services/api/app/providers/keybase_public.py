# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
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


_API_ENDPOINT = "https://keybase.io/_/api/1.0/user/lookup.json"
_MAX_RAW_RESPONSE_BYTES = 16 * 1024
_USERNAME_RE = re.compile(r"^[a-z0-9_]+$")
_UID_RE = re.compile(r"^[0-9a-f]{32}$")

KeybaseFetch = Callable[[str], Awaitable[dict[str, object] | None]]


def keybase_username_from_seed(value: str) -> str | None:
    """Return a Keybase username only when the supplied username is already canonical."""

    if _USERNAME_RE.fullmatch(value) is None:
        return None
    return value


def _retry_after(exc: HTTPError) -> float | None:
    raw = exc.headers.get("Retry-After") if exc.headers is not None else None
    if raw is None:
        return None
    try:
        value = float(raw)
    except ValueError:
        return None
    return value if value >= 0 else None


def _fetch_keybase_public_user_sync(username: str) -> dict[str, object] | None:
    request_url = f"{_API_ENDPOINT}?{urlencode({'usernames': username, 'fields': 'basics'})}"
    request = Request(
        request_url,
        headers={
            "Accept": "application/json",
            "User-Agent": "PersonaLattice/0.0.1 public-keybase-user-research",
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
            raise ProviderTransientError("Keybase public-user API was unavailable.") from exc
        raise ProviderExecutionError("Keybase public-user API rejected the request.") from exc
    except (URLError, TimeoutError) as exc:
        raise ProviderTransientError("Keybase public-user API was unavailable.") from exc

    if len(raw) > _MAX_RAW_RESPONSE_BYTES:
        raise ProviderResponseTooLarge("Keybase public-user API response exceeded the adapter limit.")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProviderResultValidationError("Keybase public-user API returned invalid JSON.") from exc
    if not isinstance(payload, dict):
        raise ProviderResultValidationError("Keybase public-user API returned an invalid response shape.")

    status = payload.get("status")
    if not isinstance(status, dict) or status.get("code") != 0:
        raise ProviderExecutionError("Keybase public-user API returned a non-success status.")
    users = payload.get("them")
    if not isinstance(users, list) or len(users) != 1:
        raise ProviderResultValidationError("Keybase public-user API returned an invalid result cardinality.")
    user = users[0]
    if user is None:
        return None
    if not isinstance(user, dict):
        raise ProviderResultValidationError("Keybase public-user API returned an invalid user shape.")
    return user


async def fetch_keybase_public_user(username: str) -> dict[str, object] | None:
    return await asyncio.to_thread(_fetch_keybase_public_user_sync, username)


def _validated_details(user: dict[str, object], *, expected_username: str) -> dict[str, object]:
    top_level_id = user.get("id")
    basics = user.get("basics")
    if not isinstance(basics, dict):
        raise ProviderResultValidationError("Keybase public user is missing basics.")

    username = basics.get("username")
    if username != expected_username:
        raise ProviderResultValidationError("Keybase returned a different username.")

    basics_uid = basics.get("uid")
    uid = basics_uid if isinstance(basics_uid, str) else top_level_id
    if not isinstance(uid, str) or _UID_RE.fullmatch(uid) is None:
        raise ProviderResultValidationError("Keybase public user has an invalid uid.")
    if isinstance(top_level_id, str) and top_level_id != uid:
        raise ProviderResultValidationError("Keybase public user id fields disagree.")
    if isinstance(basics_uid, str) and basics_uid != uid:
        raise ProviderResultValidationError("Keybase public user uid fields disagree.")

    ctime = basics.get("ctime")
    if not isinstance(ctime, int) or isinstance(ctime, bool) or ctime < 0:
        raise ProviderResultValidationError("Keybase public user has an invalid creation timestamp.")

    return {
        "keybase_username": username,
        "keybase_uid": uid,
        "account_created_at": ctime,
        "account_candidate": True,
        "identity_claim": False,
        "field_visibility": "public_directory_basics",
    }


class KeybasePublicUserProvider:
    descriptor = PROVIDER_BY_NAME["keybase_public_user"]

    def __init__(self, *, fetcher: KeybaseFetch = fetch_keybase_public_user) -> None:
        self.fetcher = fetcher

    async def execute(self, query: ProviderQuery, secret: str | None) -> ProviderResult:
        if secret is not None:
            raise ProviderValidationError("Keybase public-user lookup does not accept credentials.")
        if query.identifier_kind != "username":
            raise ProviderValidationError("Keybase public-user lookup only accepts usernames.")

        username = keybase_username_from_seed(query.identifier_value)
        if username is None:
            raise ProviderValidationError("Keybase public-user lookup requires a canonical lowercase username.")

        user = await self.fetcher(username)
        if user is None:
            return ProviderResult(observations=())
        details = _validated_details(user, expected_username=username)
        return ProviderResult(
            observations=(
                ProviderObservationData(
                    source_locator=f"https://keybase.io/{username}",
                    payload=details,
                ),
            )
        )
