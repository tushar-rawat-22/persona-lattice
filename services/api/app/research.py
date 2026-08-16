# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import StrEnum
from urllib.parse import quote, urlsplit
from uuid import uuid4

from phonenumbers import carrier, geocoder, timezone

from .evidence import IdentifierKind, normalize_identifier
from .models import Purpose
from .network_metadata import resolve_public_host_ips
from .providers.base import ProviderObservationData, ProviderQuery
from .providers.contracts import ExecutionRequest
from .providers.github_public import GitHubPublicProfileProvider, fetch_github_public_profile
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
_DEFAULT_GITHUB_PROVIDER = GitHubPublicProfileProvider()
_GITHUB_RUNTIME = ProviderRuntime(adapters=[_DEFAULT_GITHUB_PROVIDER])


def _sherlock_observation_from_provider(item: ProviderObservationData) -> QuickObservation:
    state = str(item.payload.get("account_state", "unknown"))
    site = str(item.payload.get("site", "public account"))
    return QuickObservation(
        source="sherlock",
        source_locator=item.source_locator,
        summary=f"{site}: {state}",
        details=dict(item.payload),
    )


def _github_observation_from_provider(item: ProviderObservationData) -> QuickObservation:
    login = str(item.payload.get("login", "public account"))
    return QuickObservation(
        source="github_public_api",
        source_locator=item.source_locator,
        summary=f"GitHub public profile for @{login}; same-handle account candidate only.",
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


async def lookup_github_public_profile(username: str) -> dict[str, object] | None:
    """Compatibility helper for callers needing the raw public GitHub payload.

    Production quick research does not call this helper; it uses the governed
    GitHub provider/runtime path below.
    """

    return await fetch_github_public_profile(username)


def _legacy_github_observation(payload: dict[str, object]) -> QuickObservation | None:
    """Convert an explicitly injected legacy test lookup without widening fields."""

    login = payload.get("login")
    html_url = payload.get("html_url")
    if not isinstance(login, str) or not isinstance(html_url, str):
        return None

    allowed_fields = (
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


async def _github_observations(
    normalized_value: str,
    *,
    subject_id,
    identifier_id,
    purpose: Purpose,
    consent_acknowledged: bool,
    injected_lookup: PublicLookup | None,
) -> list[QuickObservation]:
    if injected_lookup is not None:
        payload = await injected_lookup(normalized_value)
        if payload is None:
            return []
        observation = _legacy_github_observation(payload)
        return [] if observation is None else [observation]

    request = ExecutionRequest(
        provider_name=_DEFAULT_GITHUB_PROVIDER.descriptor.name,
        subject_id=subject_id,
        identifier_id=identifier_id,
        purpose=purpose,
        consent_acknowledged=consent_acknowledged,
    )
    result = await _GITHUB_RUNTIME.execute(
        request=request,
        query=ProviderQuery(
            subject_id=subject_id,
            identifier_id=identifier_id,
            identifier_kind=IdentifierKind.USERNAME.value,
            identifier_value=normalized_value,
        ),
    )
    return [_github_observation_from_provider(item) for item in result.observations]


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
    github_lookup: PublicLookup | None = None,
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

    observations = [_sherlock_observation_from_provider(item) for item in result.observations]
    warnings: list[str] = []
    enrichments = await asyncio.gather(
        _github_observations(
            normalized_value,
            subject_id=subject_id,
            identifier_id=identifier_id,
            purpose=purpose,
            consent_acknowledged=consent_acknowledged,
            injected_lookup=github_lookup,
        ),
        gitlab_lookup(normalized_value),
        codeforces_lookup(normalized_value),
        return_exceptions=True,
    )
    github_observations, gitlab_payload, codeforces_payload = enrichments

    if isinstance(github_observations, Exception):
        warnings.append("GitHub public profile enrichment was temporarily unavailable.")
    else:
        observations.extend(github_observations)

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
                    summary=(
                        "Globally reachable addresses for the public hostname; "
                        "website infrastructure only."
                    ),
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
    github_lookup: PublicLookup | None = None,
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
