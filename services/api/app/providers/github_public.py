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
    ProviderResultValidationError,
    ProviderTransientError,
    ProviderValidationError,
)
from .registry import PROVIDER_BY_NAME


_GITHUB_API_VERSION = "2026-03-10"
_MAX_RAW_RESPONSE_BYTES = 64 * 1024
_GITHUB_RESERVED_PROFILE_SEGMENTS = frozenset(
    {
        "about",
        "account",
        "collections",
        "contact",
        "customer-stories",
        "enterprise",
        "events",
        "explore",
        "features",
        "issues",
        "login",
        "marketplace",
        "new",
        "notifications",
        "organizations",
        "orgs",
        "pricing",
        "pulls",
        "readme",
        "search",
        "security",
        "settings",
        "signup",
        "site",
        "sponsors",
        "topics",
        "trending",
    }
)
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


def _fetch_github_json_sync(url: str, *, resource_name: str) -> dict[str, object] | None:
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "PersonaLattice/0.0.1 public-source-research",
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
            raise ProviderTransientError(f"GitHub {resource_name} endpoint was unavailable.") from exc
        raise ProviderExecutionError(f"GitHub {resource_name} request failed.") from exc
    except (URLError, TimeoutError) as exc:
        raise ProviderTransientError(f"GitHub {resource_name} request failed.") from exc

    if len(raw) > _MAX_RAW_RESPONSE_BYTES:
        raise ProviderValidationError(f"GitHub {resource_name} response exceeded the adapter limit.")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProviderValidationError(f"GitHub {resource_name} returned invalid JSON.") from exc
    if not isinstance(payload, dict):
        raise ProviderValidationError(f"GitHub {resource_name} returned an invalid response shape.")
    return payload


def _fetch_github_public_profile_sync(username: str) -> dict[str, object] | None:
    return _fetch_github_json_sync(
        f"https://api.github.com/users/{quote(username, safe='')}",
        resource_name="public profile",
    )


async def fetch_github_public_profile(username: str) -> dict[str, object] | None:
    return await asyncio.to_thread(_fetch_github_public_profile_sync, username)


def github_profile_username_from_url(value: str) -> str | None:
    """Return the login from an exact canonical GitHub public profile URL."""

    parts = urlsplit(value)
    if (
        parts.scheme != "https"
        or parts.hostname is None
        or parts.hostname.casefold() != "github.com"
        or parts.username is not None
        or parts.password is not None
        or parts.port is not None
        or parts.query
        or parts.fragment
    ):
        return None
    segments = [segment for segment in parts.path.split("/") if segment]
    if len(segments) != 1:
        return None
    login = segments[0]
    if parts.path not in {f"/{login}", f"/{login}/"} or "%" in login:
        return None
    if login.casefold() in _GITHUB_RESERVED_PROFILE_SEGMENTS:
        return None
    return login


def github_repository_from_url(value: str) -> tuple[str, str] | None:
    """Return the exact GitHub repository owner/name for a canonical public URL."""

    parts = urlsplit(value)
    if (
        parts.scheme != "https"
        or parts.hostname is None
        or parts.hostname.casefold() != "github.com"
        or parts.username is not None
        or parts.password is not None
        or parts.port is not None
        or parts.query
        or parts.fragment
    ):
        return None
    segments = [segment for segment in parts.path.split("/") if segment]
    if len(segments) != 2:
        return None
    owner, repository = segments
    if parts.path not in {f"/{owner}/{repository}", f"/{owner}/{repository}/"}:
        return None
    return owner, repository


def _fetch_github_public_repository_sync(owner: str, repository: str) -> dict[str, object] | None:
    return _fetch_github_json_sync(
        f"https://api.github.com/repos/{quote(owner, safe='')}/{quote(repository, safe='')}",
        resource_name="public repository",
    )


async def fetch_github_public_repository(owner: str, repository: str) -> dict[str, object] | None:
    return await asyncio.to_thread(_fetch_github_public_repository_sync, owner, repository)


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
        or parts.port is not None
        or not parts.path.strip("/")
        or parts.query
        or parts.fragment
    ):
        raise ProviderValidationError("GitHub public profile returned an invalid public profile URL.")
    expected_path = f"/{username}".casefold()
    if parts.path.rstrip("/").casefold() != expected_path:
        raise ProviderValidationError("GitHub public profile URL does not match the requested username.")
    return value


def _validated_repository_url(value: object, *, owner: str, repository: str) -> str:
    if not isinstance(value, str):
        raise ProviderValidationError("GitHub public repository is missing html_url.")
    parsed = github_repository_from_url(value)
    if parsed is None:
        raise ProviderValidationError("GitHub public repository returned an invalid public repository URL.")
    returned_owner, returned_repository = parsed
    if returned_owner.casefold() != owner.casefold() or returned_repository.casefold() != repository.casefold():
        raise ProviderValidationError("GitHub public repository URL does not match the requested repository.")
    return value


class GitHubPublicProfileProvider:
    descriptor = PROVIDER_BY_NAME["github_public_api"]

    def __init__(
        self,
        *,
        fetcher: GitHubFetch = fetch_github_public_profile,
        repository_fetcher: Callable[[str, str], Awaitable[dict[str, object] | None]] = fetch_github_public_repository,
    ) -> None:
        self.fetcher = fetcher
        self.repository_fetcher = repository_fetcher

    async def execute(self, query: ProviderQuery, secret: str | None) -> ProviderResult:
        if secret is not None:
            raise ProviderValidationError("GitHub public lookup does not accept credentials.")
        if query.identifier_kind == "username":
            return await self._execute_profile(query, username=query.identifier_value)
        if query.identifier_kind == "url":
            profile_username = github_profile_username_from_url(query.identifier_value)
            if profile_username is not None:
                return await self._execute_profile(query, username=profile_username)
            return await self._execute_repository(query)
        raise ProviderValidationError(
            "GitHub public lookup only accepts usernames or exact public profile/repository URLs."
        )

    async def _execute_profile(self, query: ProviderQuery, *, username: str) -> ProviderResult:
        payload = await self.fetcher(username)
        if payload is None:
            return ProviderResult(observations=())

        login = payload.get("login")
        if not isinstance(login, str) or login.casefold() != username.casefold():
            raise ProviderValidationError("GitHub public profile login does not match the requested username.")
        account_type = payload.get("type")
        if account_type != "User":
            raise ProviderResultValidationError(
                "GitHub username lookup did not return a personal User account."
            )
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

    async def _execute_repository(self, query: ProviderQuery) -> ProviderResult:
        parsed = github_repository_from_url(query.identifier_value)
        if parsed is None:
            raise ProviderValidationError(
                "GitHub URL lookup requires an exact public profile or repository URL."
            )
        owner, repository = parsed
        payload = await self.repository_fetcher(owner, repository)
        if payload is None:
            return ProviderResult(observations=())

        full_name = payload.get("full_name")
        expected_full_name = f"{owner}/{repository}"
        if not isinstance(full_name, str) or full_name.casefold() != expected_full_name.casefold():
            raise ProviderValidationError("GitHub public repository full_name does not match the requested repository.")
        if payload.get("private") is not False:
            raise ProviderValidationError("GitHub repository result was not explicitly public.")

        owner_payload = payload.get("owner")
        if not isinstance(owner_payload, dict):
            raise ProviderValidationError("GitHub public repository is missing owner metadata.")
        owner_login = owner_payload.get("login")
        if not isinstance(owner_login, str) or owner_login.casefold() != owner.casefold():
            raise ProviderValidationError("GitHub public repository owner does not match the requested owner.")
        owner_type = owner_payload.get("type")
        if owner_type is not None and owner_type not in {"User", "Organization"}:
            raise ProviderValidationError("GitHub public repository returned an unsupported owner type.")

        source_locator = _validated_repository_url(payload.get("html_url"), owner=owner, repository=repository)
        fork = payload.get("fork")
        archived = payload.get("archived")
        if fork is not None and not isinstance(fork, bool):
            raise ProviderValidationError("GitHub public repository returned an invalid fork flag.")
        if archived is not None and not isinstance(archived, bool):
            raise ProviderValidationError("GitHub public repository returned an invalid archived flag.")

        details: dict[str, object] = {
            "github_repository_full_name": full_name,
            "github_repository_owner_login": owner_login,
            "github_repository_private": False,
            "identity_claim": False,
            "field_visibility": "public_repository_api",
        }
        if owner_type is not None:
            details["github_repository_owner_type"] = owner_type
        if fork is not None:
            details["github_repository_fork"] = fork
        if archived is not None:
            details["github_repository_archived"] = archived

        return ProviderResult(
            observations=(
                ProviderObservationData(
                    source_locator=source_locator,
                    payload=details,
                ),
            )
        )