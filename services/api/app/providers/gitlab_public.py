# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
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

GitLabFetch = Callable[[str, str], Awaitable[dict[str, object] | None]]


def _retry_after(exc: HTTPError) -> float | None:
    raw = exc.headers.get("Retry-After") if exc.headers is not None else None
    if raw is None:
        return None
    try:
        value = float(raw)
    except ValueError:
        return None
    return value if value >= 0 else None


def _fetch_gitlab_public_profile_sync(kind: str, value: str) -> dict[str, object] | None:
    parameter = "username" if kind == "username" else "public_email"
    query = urlencode({parameter: value})
    request = Request(
        f"https://gitlab.com/api/v4/users?{query}",
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
            raise ProviderRemoteRateLimitError(retry_after=_retry_after(exc)) from exc
        if exc.code in {408, 500, 502, 503, 504}:
            raise ProviderTransientError("GitLab public profile endpoint was unavailable.") from exc
        raise ProviderExecutionError("GitLab public profile request failed.") from exc
    except (URLError, TimeoutError) as exc:
        raise ProviderTransientError("GitLab public profile request failed.") from exc

    if len(raw) > _MAX_RAW_RESPONSE_BYTES:
        raise ProviderValidationError("GitLab public profile response exceeded the adapter limit.")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProviderValidationError("GitLab public profile returned invalid JSON.") from exc
    if not isinstance(payload, list):
        raise ProviderValidationError("GitLab public profile returned an invalid response shape.")

    for item in payload:
        if not isinstance(item, dict):
            continue
        candidate = item.get(parameter)
        if isinstance(candidate, str) and candidate.casefold() == value.casefold():
            return item
    return None


async def fetch_gitlab_public_profile(kind: str, value: str) -> dict[str, object] | None:
    return await asyncio.to_thread(_fetch_gitlab_public_profile_sync, kind, value)


def _validated_profile_url(value: object, *, username: str) -> str:
    if not isinstance(value, str):
        raise ProviderValidationError("GitLab public profile is missing web_url.")
    parts = urlsplit(value)
    if (
        parts.scheme != "https"
        or parts.hostname is None
        or parts.hostname.casefold() != "gitlab.com"
        or parts.username is not None
        or parts.password is not None
        or parts.query
        or parts.fragment
        or parts.path.rstrip("/").casefold() != f"/{username}".casefold()
    ):
        raise ProviderValidationError("GitLab public profile returned an invalid public profile URL.")
    return value


class GitLabPublicProfileProvider:
    descriptor = PROVIDER_BY_NAME["gitlab_public_api"]

    def __init__(self, *, fetcher: GitLabFetch = fetch_gitlab_public_profile) -> None:
        self.fetcher = fetcher

    async def execute(self, query: ProviderQuery, secret: str | None) -> ProviderResult:
        if secret is not None:
            raise ProviderValidationError("GitLab public profile lookup does not accept credentials.")
        if query.identifier_kind not in {"username", "email"}:
            raise ProviderValidationError("GitLab public profile lookup accepts usernames or public emails only.")

        payload = await self.fetcher(query.identifier_kind, query.identifier_value)
        if payload is None:
            return ProviderResult(observations=())

        username = payload.get("username")
        if not isinstance(username, str) or not username:
            raise ProviderValidationError("GitLab public profile is missing username.")
        if query.identifier_kind == "username" and username.casefold() != query.identifier_value.casefold():
            raise ProviderValidationError("GitLab public profile username does not match the request.")
        if query.identifier_kind == "email":
            public_email = payload.get("public_email")
            if not isinstance(public_email, str) or public_email.casefold() != query.identifier_value.casefold():
                raise ProviderValidationError("GitLab public email does not match the request.")

        source_locator = _validated_profile_url(payload.get("web_url"), username=username)
        details = {field: payload.get(field) for field in _ALLOWED_PUBLIC_FIELDS}
        details.update(
            {
                "account_candidate": True,
                "identity_claim": False,
                "field_visibility": "public_profile_api",
                "matched_by": "username" if query.identifier_kind == "username" else "exact_public_email",
            }
        )
        return ProviderResult(
            observations=(
                ProviderObservationData(source_locator=source_locator, payload=details),
            )
        )
