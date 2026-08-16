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
    ProviderTransientError,
    ProviderValidationError,
)
from .registry import PROVIDER_BY_NAME


_GITHUB_API_VERSION = "2026-03-10"
_MAX_RAW_RESPONSE_BYTES = 64 * 1024
_ALLOWED_PUBLIC_FIELDS = (
    "login",
    "id",
    "avatar_url",
    "html_url",
    "name",
    "company",
    "blog",
    "location",
    "email",
    "hireable",
    "bio",
    "twitter_username",
    "public_repos",
    "public_gists",
    "followers",
    "following",
    "created_at",
    "updated_at",
)


GitHubFetch = Callable[[str], Awaitable[dict[str, object] | None]]


def _retry_after(exc: HTTPError) -> float | None:
    raw = exc.headers.get("Retry-After") if exc.headers is not None else None
    if raw is None:
        return None
    try:
        value = float(raw)
    except ValueError:
        return None
    return value if value >= 0 else None


def _rate_limited(exc: HTTPError) -> bool:
    if exc.code == 429:
        return True
    if exc.code != 403 or exc.headers is None:
        return False
    return exc.headers.get("X-RateLimit-Remaining") == "0"


def _fetch_github_public_profile_sync(username: str) -> dict[str, object] | None:
    request = Request(
        f"https://api.github.com/users/{quote(username, safe='')}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "PersonaLattice/0.0.1 public-profile-research",
            "X-GitHub-Api-Version": _GITHUB_API_VERSION,
        },
        method="GET",
    )
    try:
        with urlopen(request, timeout=4.0) as response:
            raw = response.read(_MAX_RAW_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        if exc.code == 404:
            return None
        if _rate_limited(exc):
            raise ProviderRemoteRateLimitError(retry_after=_retry_after(exc)) from exc
        if exc.code in {408, 500, 502, 503, 504}:
            raise ProviderTransientError("GitHub public profile endpoint was unavailable.") from exc
        raise ProviderExecutionError("GitHub public profile request failed.") from exc
    except (URLError, TimeoutError) as exc:
        raise ProviderTransientError("GitHub public profile request failed.") from exc

    if len(raw) > _MAX_RAW_RESPONSE_BYTES:
        raise ProviderValidationError("GitHub public profile response exceeded the adapter limit.")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProviderValidationError("GitHub public profile returned invalid JSON.") from exc
    if not isinstance(payload, dict):
        raise ProviderValidationError("GitHub public profile returned an invalid response shape.")
    return payload


async def fetch_github_public_profile(username: str) -> dict[str, object] | None:
    return await asyncio.to_thread(_fetch_github_public_profile_sync, username)


def _validated_profile_url(value: object, *, username: str) -> str:
    if not isinstance(value, str):
        raise ProviderValidationError("GitHub public profile is missing html_url.")
    parts = urlsplit(value)
    if (
        parts.scheme != "https"
        or parts.hostname is None
        or parts.hostname.casefold() != "github.com"
        or parts.username is not None
        or parts.password is not None
        or not parts.path.strip("/")
        or parts.query
        or parts.fragment
    ):
        raise ProviderValidationError("GitHub public profile returned an invalid public profile URL.")
    expected_path = f"/{username}".casefold()
    if parts.path.rstrip("/").casefold() != expected_path:
        raise ProviderValidationError("GitHub public profile URL does not match the requested username.")
    return value


class GitHubPublicProfileProvider:
    descriptor = PROVIDER_BY_NAME["github_public_api"]

    def __init__(self, *, fetcher: GitHubFetch = fetch_github_public_profile) -> None:
        self.fetcher = fetcher

    async def execute(self, query: ProviderQuery, secret: str | None) -> ProviderResult:
        if secret is not None:
            raise ProviderValidationError("GitHub public profile lookup does not accept credentials.")
        if query.identifier_kind != "username":
            raise ProviderValidationError("GitHub public profile lookup only accepts usernames.")

        payload = await self.fetcher(query.identifier_value)
        if payload is None:
            return ProviderResult(observations=())

        login = payload.get("login")
        if not isinstance(login, str) or login.casefold() != query.identifier_value.casefold():
            raise ProviderValidationError("GitHub public profile login does not match the requested username.")
        source_locator = _validated_profile_url(payload.get("html_url"), username=login)

        details = {field: payload.get(field) for field in _ALLOWED_PUBLIC_FIELDS}
        details.update(
            {
                "account_candidate": True,
                "identity_claim": False,
                "field_visibility": "public_profile_api",
            }
        )
        return ProviderResult(
            observations=(
                ProviderObservationData(
                    source_locator=source_locator,
                    payload=details,
                ),
            )
        )
