# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import StrEnum
import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen
from uuid import uuid4

from phonenumbers import carrier, geocoder, timezone

from .evidence import IdentifierKind, normalize_identifier
from .models import Purpose
from .network_metadata import resolve_public_host_ips
from .providers.base import ProviderObservationData, ProviderQuery
from .providers.contracts import ExecutionRequest
from .providers.rate_limit import RateBudget
from .providers.runtime import ProviderRuntime
from .providers.sherlock import SherlockProvider
from .public_profiles import (
    codeforces_public_observation_fields,
    gitlab_public_observation_fields,
    lookup_codeforces_handle,
    lookup_gitlab_public_email,
    lookup_gitlab_username,
)
from .public_search import PublicSearchResult, search_exact_public_mentions


class ResearchKind(StrEnum):
    USERNAME = "username"
    PHONE = "phone"
    EMAIL = "email"
    URL = "url"


@dataclass(frozen=True, slots=True)
class QuickObservation:
    source: str
    source_locator: str
    summary: str
    details: dict[str, object]


@dataclass(frozen=True, slots=True)
class QuickResearchReport:
    kind: ResearchKind
    normalized_value: str
    observations: tuple[QuickObservation, ...]
    warnings: tuple[str, ...] = ()


PublicLookup = Callable[[str], Awaitable[dict[str, object] | None]]
PublicSearchLookup = Callable[[str], Awaitable[tuple[PublicSearchResult, ...]]]
NetworkLookup = Callable[[str], Awaitable[tuple[str, ...]]]

_DEFAULT_SHERLOCK_PROVIDER = SherlockProvider()
_SHERLOCK_RUNTIME = ProviderRuntime(adapters=[_DEFAULT_SHERLOCK_PROVIDER])
_GITHUB_BUDGET = RateBudget(limit=20, window_seconds=60.0)
_GITHUB_MAX_RESPONSE_BYTES = 64 * 1024


def _observation_from_provider(item: ProviderObservationData) -> QuickObservation:
    state = str(item.payload.get("account_state", "unknown"))
    site = str(item.payload.get("site", "public account"))
    return QuickObservation(
        source="sherlock",
        source_locator=item.source_locator,
        summary=f"{site}: {state}",
        details=dict(item.payload),
    )


def _public_search_observations(results: tuple[PublicSearchResult, ...]) -> list[QuickObservation]:
    return [
        QuickObservation(
            source="brave_public_web_index",
            source_locator=result.url,
            summary=result.title or "Exact identifier mention in the public web index.",
            details={
                "title": result.title,
                "description": result.description,
                "exact_identifier_query": True,
                "content_fetched": False,
                "identity_claim": False,
            },
        )
        for result in results
    ]


async def _public_search(
    identifier: str,
    lookup: PublicSearchLookup,
) -> tuple[list[QuickObservation], str | None]:
    try:
        results = await lookup(identifier)
    except RuntimeError:
        return [], "Licensed public-web exact-match search was temporarily unavailable."
    return _public_search_observations(results), None


def _fetch_github_public_profile_sync(username: str) -> dict[str, object] | None:
    request = Request(
        f"https://api.github.com/users/{quote(username, safe='')}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "PersonaLattice/0.0.1 public-profile-research",
            "X-GitHub-Api-Version": "2026-03-10",
        },
        method="GET",
    )
    try:
        with urlopen(request, timeout=4.0) as response:
            raw = response.read(_GITHUB_MAX_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        if exc.code == 404:
            return None
        raise RuntimeError("GitHub public profile lookup failed.") from exc
    except (URLError, TimeoutError) as exc:
        raise RuntimeError("GitHub public profile lookup failed.") from exc

    if len(raw) > _GITHUB_MAX_RESPONSE_BYTES:
        raise RuntimeError("GitHub public profile response exceeded the configured limit.")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("GitHub public profile returned invalid JSON.") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("GitHub public profile returned an invalid response shape.")
    return payload


async def lookup_github_public_profile(username: str) -> dict[str, object] | None:
    _GITHUB_BUDGET.consume()
    return await asyncio.to_thread(_fetch_github_public_profile_sync, username)


def _github_observation(payload: dict[str, object]) -> QuickObservation | None:
    login = payload.get("login")
    html_url = payload.get("html_url")
    if not isinstance(login, str) or not isinstance(html_url, str):
        return None

    allowed_fields = (
        "login", "id", "avatar_url", "html_url", "name", "company", "blog", "location",
        "email", "hireable", "bio", "twitter_username", "public_repos", "public_gists",
        "followers", "following", "created_at", "updated_at",
    )
    details = {field: payload.get(field) for field in allowed_fields}
    details.update(
        {
            "account_candidate": True,
            "identity_claim": False,
            "field_visibility": "public_profile_api",
        }
    )
    return QuickObservation(
        source="github_public_api",
        source_locator=html_url,
        summary=f"GitHub public profile for @{login}; same-handle account candidate only.",
        details=details,
    )


def _gitlab_observation(payload: dict[str, object], *, matched_by: str) -> QuickObservation | None:
    username = payload.get("username")
    web_url = payload.get("web_url")
    if not isinstance(username, str) or not isinstance(web_url, str):
        return None
    details = gitlab_public_observation_fields(payload)
    details.update(
        {
            "account_candidate": True,
            "identity_claim": False,
            "field_visibility": "public_profile_api",
            "matched_by": matched_by,
        }
    )
    return QuickObservation(
        source="gitlab_public_api",
        source_locator=web_url,
        summary=f"GitLab public profile matched by {matched_by}; account candidate only.",
        details=details,
    )


def _codeforces_observation(payload: dict[str, object]) -> QuickObservation | None:
    handle = payload.get("handle")
    if not isinstance(handle, str):
        return None
    details = codeforces_public_observation_fields(payload)
    details.update(
        {
            "account_candidate": True,
            "identity_claim": False,
            "field_visibility": "public_profile_api",
        }
    )
    return QuickObservation(
        source="codeforces_public_api",
        source_locator=f"https://codeforces.com/profile/{quote(handle, safe='')}",
        summary=f"Codeforces public profile for @{handle}; same-handle account candidate only.",
        details=details,
    )


async def _research_username(
    normalized_value: str,
    *,
    purpose: Purpose,
    consent_acknowledged: bool,
    provider: SherlockProvider | None = None,
    github_lookup: PublicLookup = lookup_github_public_profile,
    gitlab_lookup: PublicLookup = lookup_gitlab_username,
    codeforces_lookup: PublicLookup = lookup_codeforces_handle,
    public_search_lookup: PublicSearchLookup = search_exact_public_mentions,
) -> QuickResearchReport:
    adapter = provider or _DEFAULT_SHERLOCK_PROVIDER
    runtime = _SHERLOCK_RUNTIME if provider is None else ProviderRuntime(adapters=[adapter])
    subject_id = uuid4()
    identifier_id = uuid4()
    request = ExecutionRequest(
        provider_name=adapter.descriptor.name,
        subject_id=subject_id,
        identifier_id=identifier_id,
        purpose=purpose,
        consent_acknowledged=consent_acknowledged,
    )
    result = await runtime.execute(
        request=request,
        query=ProviderQuery(
            subject_id=subject_id,
            identifier_id=identifier_id,
            identifier_kind=IdentifierKind.USERNAME.value,
            identifier_value=normalized_value,
        ),
    )

    observations = [_observation_from_provider(item) for item in result.observations]
    warnings: list[str] = []
    enrichments = await asyncio.gather(
        github_lookup(normalized_value),
        gitlab_lookup(normalized_value),
        codeforces_lookup(normalized_value),
        return_exceptions=True,
    )
    github_payload, gitlab_payload, codeforces_payload = enrichments

    if isinstance(github_payload, Exception):
        warnings.append("GitHub public profile enrichment was temporarily unavailable.")
    elif github_payload is not None:
        enriched = _github_observation(github_payload)
        if enriched is not None:
            observations.append(enriched)

    if isinstance(gitlab_payload, Exception):
        warnings.append("GitLab public profile enrichment was temporarily unavailable.")
    elif gitlab_payload is not None:
        enriched = _gitlab_observation(gitlab_payload, matched_by="username")
        if enriched is not None:
            observations.append(enriched)

    if isinstance(codeforces_payload, Exception):
        warnings.append("Codeforces public profile enrichment was temporarily unavailable.")
    elif codeforces_payload is not None:
        enriched = _codeforces_observation(codeforces_payload)
        if enriched is not None:
            observations.append(enriched)

    search_observations, search_warning = await _public_search(normalized_value, public_search_lookup)
    observations.extend(search_observations)
    if search_warning:
        warnings.append(search_warning)

    return QuickResearchReport(
        kind=ResearchKind.USERNAME,
        normalized_value=normalized_value,
        observations=tuple(observations),
        warnings=tuple(warnings),
    )


async def _research_phone(
    normalized_value: str,
    *,
    public_search_lookup: PublicSearchLookup = search_exact_public_mentions,
) -> QuickResearchReport:
    import phonenumbers

    parsed = phonenumbers.parse(normalized_value, None)
    region = geocoder.description_for_number(parsed, "en") or None
    network = carrier.name_for_number(parsed, "en") or None
    timezones = tuple(timezone.time_zones_for_number(parsed))
    details: dict[str, object] = {
        "country_code": parsed.country_code,
        "national_number": str(parsed.national_number),
        "possible": phonenumbers.is_possible_number(parsed),
        "valid": phonenumbers.is_valid_number(parsed),
        "region": region,
        "carrier": network,
        "timezones": timezones,
        "personal_identity_claim": False,
    }
    observations = [
        QuickObservation(
            source="libphonenumber_metadata",
            source_locator="local://libphonenumber",
            summary="Numbering-plan metadata; not subscriber identity.",
            details=details,
        )
    ]
    warnings: list[str] = []
    search_observations, search_warning = await _public_search(normalized_value, public_search_lookup)
    observations.extend(search_observations)
    if search_warning:
        warnings.append(search_warning)
    return QuickResearchReport(
        kind=ResearchKind.PHONE,
        normalized_value=normalized_value,
        observations=tuple(observations),
        warnings=tuple(warnings),
    )


async def _research_email(
    normalized_value: str,
    *,
    gitlab_email_lookup: PublicLookup = lookup_gitlab_public_email,
    public_search_lookup: PublicSearchLookup = search_exact_public_mentions,
) -> QuickResearchReport:
    local_part, domain = normalized_value.rsplit("@", 1)
    observations = [
        QuickObservation(
            source="local_normalization",
            source_locator=f"domain://{domain.lower()}",
            summary="Normalized email and domain extracted locally.",
            details={
                "domain": domain.lower(),
                "local_part_length": len(local_part),
                "personal_identity_claim": False,
            },
        )
    ]
    warnings: list[str] = []
    try:
        gitlab_payload = await gitlab_email_lookup(normalized_value)
    except RuntimeError:
        gitlab_payload = None
        warnings.append("GitLab public-email lookup was temporarily unavailable.")
    if gitlab_payload is not None:
        enriched = _gitlab_observation(gitlab_payload, matched_by="exact_public_email")
        if enriched is not None:
            observations.append(enriched)

    search_observations, search_warning = await _public_search(normalized_value, public_search_lookup)
    observations.extend(search_observations)
    if search_warning:
        warnings.append(search_warning)

    if len(observations) == 1:
        warnings.append(
            "No approved external source established a public profile for this email; "
            "PersonaLattice does not infer an owner."
        )

    return QuickResearchReport(
        kind=ResearchKind.EMAIL,
        normalized_value=normalized_value,
        observations=tuple(observations),
        warnings=tuple(warnings),
    )


async def _research_url(
    normalized_value: str,
    *,
    public_search_lookup: PublicSearchLookup = search_exact_public_mentions,
    network_lookup: NetworkLookup = resolve_public_host_ips,
) -> QuickResearchReport:
    parts = urlsplit(normalized_value)
    hostname = parts.hostname or ""
    observations = [
        QuickObservation(
            source="local_normalization",
            source_locator=normalized_value,
            summary="Canonical public URL metadata extracted locally.",
            details={
                "scheme": parts.scheme,
                "hostname": parts.hostname,
                "path": parts.path,
                "personal_identity_claim": False,
            },
        )
    ]
    warnings: list[str] = []

    if hostname:
        try:
            public_ips = await network_lookup(hostname)
        except OSError:
            public_ips = ()
            warnings.append("Public DNS infrastructure lookup was temporarily unavailable.")
        if public_ips:
            observations.append(
                QuickObservation(
                    source="public_dns_infrastructure",
                    source_locator=f"dns://{hostname}",
                    summary="Globally reachable addresses for the public hostname; website infrastructure only.",
                    details={
                        "hostname": hostname,
                        "public_infrastructure_ips": list(public_ips),
                        "personal_device_ip_claim": False,
                        "physical_location_claim": False,
                    },
                )
            )

    search_observations, search_warning = await _public_search(normalized_value, public_search_lookup)
    observations.extend(search_observations)
    if search_warning:
        warnings.append(search_warning)

    return QuickResearchReport(
        kind=ResearchKind.URL,
        normalized_value=normalized_value,
        observations=tuple(observations),
        warnings=tuple(warnings),
    )


async def run_quick_research(
    *,
    kind: ResearchKind,
    value: str,
    purpose: Purpose,
    consent_acknowledged: bool,
    sherlock_provider: SherlockProvider | None = None,
    github_lookup: PublicLookup = lookup_github_public_profile,
    gitlab_lookup: PublicLookup = lookup_gitlab_username,
    codeforces_lookup: PublicLookup = lookup_codeforces_handle,
    gitlab_email_lookup: PublicLookup = lookup_gitlab_public_email,
    public_search_lookup: PublicSearchLookup = search_exact_public_mentions,
    network_lookup: NetworkLookup = resolve_public_host_ips,
) -> QuickResearchReport:
    identifier_kind = IdentifierKind(kind.value)
    normalized = normalize_identifier(identifier_kind, value)

    if kind is ResearchKind.USERNAME:
        return await _research_username(
            normalized.normalized_value,
            purpose=purpose,
            consent_acknowledged=consent_acknowledged,
            provider=sherlock_provider,
            github_lookup=github_lookup,
            gitlab_lookup=gitlab_lookup,
            codeforces_lookup=codeforces_lookup,
            public_search_lookup=public_search_lookup,
        )
    if kind is ResearchKind.PHONE:
        return await _research_phone(
            normalized.normalized_value,
            public_search_lookup=public_search_lookup,
        )
    if kind is ResearchKind.EMAIL:
        return await _research_email(
            normalized.normalized_value,
            gitlab_email_lookup=gitlab_email_lookup,
            public_search_lookup=public_search_lookup,
        )
    if kind is ResearchKind.URL:
        return await _research_url(
            normalized.normalized_value,
            public_search_lookup=public_search_lookup,
            network_lookup=network_lookup,
        )
    raise ValueError("Unsupported research kind.")
