# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import asyncio
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .providers.codeforces_public import fetch_codeforces_public_profile
from .providers.rate_limit import RateBudget


_MAX_RESPONSE_BYTES = 96 * 1024
_TIMEOUT_SECONDS = 4.0
_GITLAB_BUDGET = RateBudget(limit=20, window_seconds=60.0)


def _fetch_json(url: str, *, user_agent: str) -> object:
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": user_agent,
        },
        method="GET",
    )
    try:
        with urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
            raw = response.read(_MAX_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        if exc.code == 404:
            return None
        raise RuntimeError("Public profile lookup failed.") from exc
    except (URLError, TimeoutError) as exc:
        raise RuntimeError("Public profile lookup failed.") from exc

    if len(raw) > _MAX_RESPONSE_BYTES:
        raise RuntimeError("Public profile response exceeded the configured limit.")
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("Public profile source returned invalid JSON.") from exc


def _gitlab_user(payload: object, *, username: str | None = None, public_email: str | None = None) -> dict[str, object] | None:
    if not isinstance(payload, list):
        raise RuntimeError("GitLab public user lookup returned an invalid response shape.")
    for item in payload:
        if not isinstance(item, dict):
            continue
        item_username = item.get("username")
        item_email = item.get("public_email")
        if username is not None and (
            not isinstance(item_username, str) or item_username.casefold() != username.casefold()
        ):
            continue
        if public_email is not None and (
            not isinstance(item_email, str) or item_email.casefold() != public_email.casefold()
        ):
            continue
        return item
    return None


def _gitlab_username_sync(username: str) -> dict[str, object] | None:
    query = urlencode({"username": username})
    payload = _fetch_json(
        f"https://gitlab.com/api/v4/users?{query}",
        user_agent="PersonaLattice/0.0.1 public-profile-research",
    )
    return _gitlab_user(payload, username=username)


async def lookup_gitlab_username(username: str) -> dict[str, object] | None:
    _GITLAB_BUDGET.consume()
    return await asyncio.to_thread(_gitlab_username_sync, username)


def _gitlab_public_email_sync(email: str) -> dict[str, object] | None:
    query = urlencode({"public_email": email})
    payload = _fetch_json(
        f"https://gitlab.com/api/v4/users?{query}",
        user_agent="PersonaLattice/0.0.1 public-profile-research",
    )
    return _gitlab_user(payload, public_email=email)


async def lookup_gitlab_public_email(email: str) -> dict[str, object] | None:
    _GITLAB_BUDGET.consume()
    return await asyncio.to_thread(_gitlab_public_email_sync, email)


async def lookup_codeforces_handle(handle: str) -> dict[str, object] | None:
    """Compatibility helper for callers needing the raw public Codeforces payload.

    Production quick research does not call this helper directly; it executes the
    Codeforces adapter through the shared governed ProviderRuntime.
    """

    return await fetch_codeforces_public_profile(handle)


def gitlab_public_observation_fields(payload: dict[str, object]) -> dict[str, object]:
    allowed = (
        "id",
        "username",
        "name",
        "state",
        "locked",
        "avatar_url",
        "web_url",
        "created_at",
        "bio",
        "location",
        "public_email",
        "linkedin",
        "twitter",
        "discord",
        "website_url",
        "organization",
        "job_title",
        "pronouns",
    )
    return {field: payload.get(field) for field in allowed}


def codeforces_public_observation_fields(payload: dict[str, object]) -> dict[str, object]:
    allowed = (
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
    return {field: payload.get(field) for field in allowed}
