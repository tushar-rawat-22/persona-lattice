# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlsplit
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


def _read_json_response(request: Request, *, context: str) -> object:
    try:
        with urlopen(request, timeout=4.0) as response:
            raw = response.read(_MAX_RAW_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        if exc.code == 404:
            return None
        if exc.code == 429:
            raise ProviderRemoteRateLimitError(retry_after=_retry_after(exc)) from exc
        if exc.code in {408, 500, 502, 503, 504}:
            raise ProviderTransientError(f"GitLab {context} endpoint was unavailable.") from exc
        raise ProviderExecutionError(f"GitLab {context} request failed.") from exc
    except (URLError, TimeoutError) as exc:
        raise ProviderTransientError(f"GitLab {context} request failed.") from exc

    if len(raw) > _MAX_RAW_RESPONSE_BYTES:
        raise ProviderValidationError(f"GitLab {context} response exceeded the adapter limit.")
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProviderValidationError(f"GitLab {context} returned invalid JSON.") from exc


def _fetch_gitlab_public_profile_sync(kind: str, value: str) -> dict[str, object] | None:
    parameter = "username" if kind == "username" else "public_email"
    query = urlencode({parameter: value, "humans": "true"})
    request = Request(
        f"https://gitlab.com/api/v4/users?{query}",
        headers={
            "Accept": "application/json",
            "User-Agent": "PersonaLattice/0.0.1 public-profile-research",
        },
        method="GET",
    )
    payload = _read_json_response(request, context="public profile")
    if payload is None:
        return None
    if not isinstance(payload, list):
        raise ProviderValidationError("GitLab public profile returned an invalid response shape.")

    for item in payload:
        if not isinstance(item, dict):
            continue
        candidate = item.get(parameter)
        if isinstance(candidate, str) and candidate.casefold() == value.casefold():
            return item
    return None


def gitlab_project_path_from_url(value: str) -> str | None:
    parts = urlsplit(value)
    if (
        parts.scheme != "https"
        or parts.hostname is None
        or parts.hostname.casefold() != "gitlab.com"
        or parts.username is not None
        or parts.password is not None
        or parts.port is not None
        or parts.query
        or parts.fragment
    ):
        return None

    raw_segments = parts.path.split("/")
    if not raw_segments or raw_segments[0] != "":
        return None
    segments = raw_segments[1:]
    if len(segments) < 2 or any(not segment for segment in segments):
        return None
    if segments[0].casefold() == "o":
        return None
    if any(segment in {"-", "."} for segment in segments):
        return None
    if segments[-1].casefold().endswith(".git"):
        return None
    return "/".join(segments)


def _fetch_gitlab_public_project_sync(value: str) -> dict[str, object] | None:
    project_path = gitlab_project_path_from_url(value)
    if project_path is None:
        raise ProviderValidationError("GitLab project lookup requires an exact public project URL.")
    encoded = quote(project_path, safe="")
    request = Request(
        f"https://gitlab.com/api/v4/projects/{encoded}",
        headers={
            "Accept": "application/json",
            "User-Agent": "PersonaLattice/0.0.1 public-project-research",
        },
        method="GET",
    )
    payload = _read_json_response(request, context="public project")
    if payload is None:
        return None
    if not isinstance(payload, dict):
        raise ProviderValidationError("GitLab public project returned an invalid response shape.")
    return payload


async def fetch_gitlab_public(kind: str, value: str) -> dict[str, object] | None:
    if kind == "url":
        return await asyncio.to_thread(_fetch_gitlab_public_project_sync, value)
    return await asyncio.to_thread(_fetch_gitlab_public_profile_sync, kind, value)


async def fetch_gitlab_public_profile(kind: str, value: str) -> dict[str, object] | None:
    """Compatibility helper for existing username/public-email callers."""
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
        or parts.port is not None
        or parts.query
        or parts.fragment
        or parts.path.rstrip("/").casefold() != f"/{username}".casefold()
    ):
        raise ProviderValidationError("GitLab public profile returned an invalid public profile URL.")
    return value


def _validated_project_url(value: object, *, project_path: str) -> str:
    if not isinstance(value, str):
        raise ProviderValidationError("GitLab public project is missing web_url.")
    parts = urlsplit(value)
    returned_path = gitlab_project_path_from_url(value)
    if (
        parts.path.casefold() != f"/{project_path}".casefold()
        or returned_path is None
        or returned_path.casefold() != project_path.casefold()
    ):
        raise ProviderValidationError("GitLab public project returned an invalid canonical project URL.")
    return value


def _project_observation(payload: dict[str, object], *, requested_path: str) -> ProviderResult:
    project_id = payload.get("id")
    if not isinstance(project_id, int) or isinstance(project_id, bool) or project_id <= 0:
        raise ProviderValidationError("GitLab public project is missing a valid numeric project ID.")

    path_with_namespace = payload.get("path_with_namespace")
    if not isinstance(path_with_namespace, str) or not path_with_namespace:
        raise ProviderValidationError("GitLab public project is missing path_with_namespace.")
    if path_with_namespace.casefold() != requested_path.casefold():
        raise ProviderValidationError("GitLab public project path does not match the request.")

    visibility = payload.get("visibility")
    if visibility != "public":
        raise ProviderValidationError("GitLab project lookup returned a non-public project.")

    namespace = payload.get("namespace")
    if not isinstance(namespace, dict):
        raise ProviderValidationError("GitLab public project is missing namespace metadata.")
    namespace_kind = namespace.get("kind")
    namespace_full_path = namespace.get("full_path")
    if namespace_kind not in {"user", "group"}:
        raise ProviderValidationError("GitLab public project returned an invalid namespace kind.")
    if not isinstance(namespace_full_path, str) or not namespace_full_path:
        raise ProviderValidationError("GitLab public project returned an invalid namespace path.")
    requested_namespace = requested_path.rsplit("/", 1)[0]
    if namespace_full_path.casefold() != requested_namespace.casefold():
        raise ProviderValidationError("GitLab public project namespace does not match the request.")

    source_locator = _validated_project_url(payload.get("web_url"), project_path=path_with_namespace)
    archived = payload.get("archived")
    if archived is not None and not isinstance(archived, bool):
        raise ProviderValidationError("GitLab public project returned an invalid archived flag.")

    details: dict[str, object] = {
        "gitlab_project_id": project_id,
        "gitlab_project_path_with_namespace": path_with_namespace,
        "gitlab_project_visibility": visibility,
        "gitlab_project_namespace_kind": namespace_kind,
        "gitlab_project_namespace_full_path": namespace_full_path,
        "gitlab_project_archived": archived,
        "identity_claim": False,
        "field_visibility": "public_project_api",
        "matched_by": "exact_project_url",
    }
    return ProviderResult(
        observations=(ProviderObservationData(source_locator=source_locator, payload=details),)
    )


class GitLabPublicProfileProvider:
    descriptor = PROVIDER_BY_NAME["gitlab_public_api"]

    def __init__(self, *, fetcher: GitLabFetch = fetch_gitlab_public) -> None:
        self.fetcher = fetcher

    async def execute(self, query: ProviderQuery, secret: str | None) -> ProviderResult:
        if secret is not None:
            raise ProviderValidationError("GitLab public lookup does not accept credentials.")
        if query.identifier_kind not in {"username", "email", "url"}:
            raise ProviderValidationError(
                "GitLab public lookup accepts usernames, public emails, or exact project URLs only."
            )

        if query.identifier_kind == "url":
            project_path = gitlab_project_path_from_url(query.identifier_value)
            if project_path is None:
                raise ProviderValidationError("GitLab project lookup requires an exact public project URL.")
            payload = await self.fetcher(query.identifier_kind, query.identifier_value)
            if payload is None:
                return ProviderResult(observations=())
            return _project_observation(payload, requested_path=project_path)

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
