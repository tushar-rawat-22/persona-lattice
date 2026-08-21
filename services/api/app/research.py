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
from .intelligence.contracts import LeadKind
from .intelligence.source_outcomes import (
    source_execution_failure_record,
    source_local_budget_record,
    source_optional_not_configured_record,
    source_provider_exception_record,
    source_result_record,
)
from .intelligence.source_states import SourceRunRecord, SourceRunState
from .models import Purpose
from .network_metadata import resolve_public_host_ips
from .providers.base import ProviderObservationData, ProviderQuery
from .providers.bluesky_admission import BlueskyAdmissionError, normalize_bluesky_handle
from .providers.contracts import ExecutionRequest
from .providers.crossref_work import crossref_doi_from_url
from .providers.errors import ProviderRateBudgetExceeded
from .providers.github_public import fetch_github_public_profile
from .providers.keybase_public import keybase_username_from_seed
from .providers.openalex_author import openalex_author_id_from_url
from .providers.ror_organization import ror_id_from_url
from .providers.runtime import ProviderRuntime
from .providers.shared_runtime import (
    DEFAULT_BLUESKY_PROVIDER,
    DEFAULT_BRAVE_PROVIDER,
    DEFAULT_CODEFORCES_PROVIDER,
    DEFAULT_CROSSREF_PROVIDER,
    DEFAULT_DATACITE_PROVIDER,
    DEFAULT_DNS_PROVIDER,
    DEFAULT_GITHUB_PROVIDER,
    DEFAULT_GITLAB_PROVIDER,
    DEFAULT_KEYBASE_PROVIDER,
    DEFAULT_OPENALEX_PROVIDER,
    DEFAULT_PROVIDER_RUNTIME,
    DEFAULT_RDAP_PROVIDER,
    DEFAULT_ROR_PROVIDER,
    DEFAULT_SHERLOCK_PROVIDER,
    DEFAULT_STACK_OVERFLOW_PROVIDER,
    DEFAULT_WAYBACK_PROVIDER,
    DEFAULT_WIKIDATA_PROVIDER,
)
from .providers.sherlock import SherlockProvider
from .providers.stack_overflow_public import stack_overflow_user_id_from_url
from .providers.wikidata_entity import wikidata_entity_id_from_url
from .public_profiles import (
    codeforces_public_observation_fields,
    gitlab_public_observation_fields,
    lookup_codeforces_handle,
    lookup_gitlab_public_email,
    lookup_gitlab_username,
)
from .public_search import (
    PublicSearchResult,
    public_search_configured,
    search_exact_public_mentions,
)


class ResearchKind(StrEnum):
    USERNAME = "username"
    PHONE = "phone"
    EMAIL = "email"
    URL = "url"
    DOMAIN = "domain"


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
    source_runs: tuple[SourceRunRecord, ...] = ()


PublicLookup = Callable[[str], Awaitable[dict[str, object] | None]]
PublicSearchLookup = Callable[[str], Awaitable[tuple[PublicSearchResult, ...]]]
NetworkLookup = Callable[[str], Awaitable[tuple[str, ...]]]


def _source_run_for_exception(
    *,
    source_name: str,
    lead_kind: LeadKind,
    exc: BaseException,
    injected_attempt: bool = False,
) -> SourceRunRecord | None:
    """Map provider failures through the shared phase-proven source contract.

    Injected compatibility lookups execute outside ProviderRuntime, so an
    exception from one of those callables is known to be post-attempt even when
    it is not a typed provider exception.
    """

    mapped = source_provider_exception_record(
        source_name=source_name,
        lead_kind=lead_kind,
        exc=exc,
    )
    if mapped is not None:
        return mapped
    if injected_attempt:
        return source_execution_failure_record(source_name=source_name, lead_kind=lead_kind)
    return None


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


def _keybase_observation_from_provider(item: ProviderObservationData) -> QuickObservation:
    username = str(item.payload.get("keybase_username", "public account"))
    return QuickObservation(
        source="keybase_public_user",
        source_locator=item.source_locator,
        summary=f"Keybase public account basics for @{username}; same-handle account candidate only.",
        details=dict(item.payload),
    )


def _gitlab_observation_from_provider(item: ProviderObservationData) -> QuickObservation:
    matched_by = str(item.payload.get("matched_by", "public_profile"))
    return QuickObservation(
        source="gitlab_public_api",
        source_locator=item.source_locator,
        summary=f"GitLab public profile matched by {matched_by}; account candidate only.",
        details=dict(item.payload),
    )


def _codeforces_observation_from_provider(item: ProviderObservationData) -> QuickObservation:
    handle = str(item.payload.get("handle", "public account"))
    matched_by = str(item.payload.get("matched_by", "handle"))
    return QuickObservation(
        source="codeforces_public_api",
        source_locator=item.source_locator,
        summary=(
            f"Codeforces public profile for @{handle} matched by {matched_by}; "
            "account candidate only."
        ),
        details=dict(item.payload),
    )


def _bluesky_observation_from_provider(item: ProviderObservationData) -> QuickObservation:
    handle = str(item.payload.get("handle", "public account"))
    return QuickObservation(
        source="bluesky_public_profile",
        source_locator=item.source_locator,
        summary=f"Bluesky public profile for {handle}; account candidate only.",
        details=dict(item.payload),
    )


def _dns_observation_from_provider(item: ProviderObservationData) -> QuickObservation:
    return QuickObservation(
        source="public_dns_infrastructure",
        source_locator=item.source_locator,
        summary="Globally reachable addresses for the public hostname; website infrastructure only.",
        details=dict(item.payload),
    )


def _wayback_observation_from_provider(item: ProviderObservationData) -> QuickObservation:
    timestamp = str(item.payload.get("capture_timestamp", "unknown capture"))
    return QuickObservation(
        source="wayback_url_availability",
        source_locator=item.source_locator,
        summary=f"Wayback capture metadata for this exact URL at {timestamp}; archived content not fetched.",
        details=dict(item.payload),
    )


def _stack_overflow_observation_from_provider(item: ProviderObservationData) -> QuickObservation:
    user_id = str(item.payload.get("stack_overflow_user_id", "unknown"))
    return QuickObservation(
        source="stack_overflow_public_profile",
        source_locator=item.source_locator,
        summary=(
            f"Stack Overflow public profile for user {user_id}; "
            "exact profile-URL account evidence only."
        ),
        details=dict(item.payload),
    )


def _openalex_observation_from_provider(item: ProviderObservationData) -> QuickObservation:
    author_id = str(item.payload.get("openalex_author_id", "unknown"))
    return QuickObservation(
        source="openalex_exact_author",
        source_locator=item.source_locator,
        summary=(
            f"OpenAlex public scholarly metadata for author {author_id}; "
            "exact supplied-author evidence only."
        ),
        details=dict(item.payload),
    )


def _wikidata_observation_from_provider(item: ProviderObservationData) -> QuickObservation:
    entity_id = str(item.payload.get("wikidata_entity_id", "unknown"))
    return QuickObservation(
        source="wikidata_exact_entity",
        source_locator=item.source_locator,
        summary=f"Wikidata CC0 metadata for entity {entity_id}; exact supplied-entity evidence only.",
        details=dict(item.payload),
    )


def _ror_observation_from_provider(item: ProviderObservationData) -> QuickObservation:
    ror_id = str(item.payload.get("ror_id", "unknown organization"))
    return QuickObservation(
        source="ror_exact_organization",
        source_locator=item.source_locator,
        summary=f"ROR CC0 registry metadata for {ror_id}; exact supplied-organization evidence only.",
        details=dict(item.payload),
    )


def _crossref_observation_from_provider(item: ProviderObservationData) -> QuickObservation:
    doi = str(item.payload.get("crossref_doi", "unknown DOI"))
    return QuickObservation(
        source="crossref_exact_work",
        source_locator=item.source_locator,
        summary=f"Crossref bibliographic metadata for DOI {doi}; exact supplied-work evidence only.",
        details=dict(item.payload),
    )


def _datacite_observation_from_provider(item: ProviderObservationData) -> QuickObservation:
    doi = str(item.payload.get("datacite_doi", "unknown DOI"))
    return QuickObservation(
        source="datacite_exact_doi",
        source_locator=item.source_locator,
        summary=f"DataCite CC0 metadata for DOI {doi}; exact supplied-work fallback evidence only.",
        details=dict(item.payload),
    )


def _rdap_observation_from_provider(item: ProviderObservationData) -> QuickObservation:
    domain = str(item.payload.get("domain", "domain"))
    return QuickObservation(
        source="rdap_domain_registry",
        source_locator=item.source_locator,
        summary=(
            f"Authoritative public RDAP registration metadata for {domain}; "
            "registration context only."
        ),
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


def _public_search_observations_from_provider(
    items: tuple[ProviderObservationData, ...],
) -> list[QuickObservation]:
    return [
        QuickObservation(
            source="brave_public_web_index",
            source_locator=item.source_locator,
            summary=str(item.payload.get("title") or "Exact identifier mention in the public web index."),
            details=dict(item.payload),
        )
        for item in items
    ]


async def _public_search(
    identifier: str,
    lookup: PublicSearchLookup,
    *,
    lead_kind: LeadKind,
    purpose: Purpose,
    consent_acknowledged: bool,
) -> tuple[list[QuickObservation], str | None, SourceRunRecord | None]:
    if lookup is search_exact_public_mentions:
        if not public_search_configured():
            return (
                [],
                None,
                source_optional_not_configured_record(
                    source_name="brave_public_web_index",
                    lead_kind=lead_kind,
                ),
            )
        subject_id = uuid4()
        identifier_id = uuid4()
        request = ExecutionRequest(
            provider_name=DEFAULT_BRAVE_PROVIDER.descriptor.name,
            subject_id=subject_id,
            identifier_id=identifier_id,
            purpose=purpose,
            consent_acknowledged=consent_acknowledged,
        )
        try:
            result = await DEFAULT_PROVIDER_RUNTIME.execute(
                request=request,
                query=ProviderQuery(
                    subject_id=subject_id,
                    identifier_id=identifier_id,
                    identifier_kind=lead_kind.value,
                    identifier_value=identifier,
                ),
            )
        except Exception as exc:
            source_run = _source_run_for_exception(
                source_name="brave_public_web_index",
                lead_kind=lead_kind,
                exc=exc,
            )
            warning = "Licensed public-web exact-match search was temporarily unavailable."
            if isinstance(exc, ProviderRateBudgetExceeded):
                warning = "Licensed public-web exact-match search hit its local request budget."
            return [], warning, source_run

        observations = _public_search_observations_from_provider(result.observations)
        return (
            observations,
            None,
            source_result_record(
                source_name="brave_public_web_index",
                lead_kind=lead_kind,
                observation_count=len(observations),
            ),
        )

    try:
        results = await lookup(identifier)
    except ProviderRateBudgetExceeded:
        return (
            [],
            "Licensed public-web exact-match search hit its local request budget.",
            source_local_budget_record(
                source_name="brave_public_web_index",
                lead_kind=lead_kind,
            ),
        )
    except RuntimeError:
        return (
            [],
            "Licensed public-web exact-match search was temporarily unavailable.",
            source_execution_failure_record(
                source_name="brave_public_web_index",
                lead_kind=lead_kind,
            ),
        )
    observations = _public_search_observations(results)
    return (
        observations,
        None,
        source_result_record(
            source_name="brave_public_web_index",
            lead_kind=lead_kind,
            observation_count=len(observations),
        ),
    )


async def lookup_github_public_profile(username: str) -> dict[str, object] | None:
    """Compatibility helper for callers needing the raw public GitHub payload."""
    return await fetch_github_public_profile(username)


def _legacy_github_observation(payload: dict[str, object]) -> QuickObservation | None:
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
        provider_name=DEFAULT_GITHUB_PROVIDER.descriptor.name,
        subject_id=subject_id,
        identifier_id=identifier_id,
        purpose=purpose,
        consent_acknowledged=consent_acknowledged,
    )
    result = await DEFAULT_PROVIDER_RUNTIME.execute(
        request=request,
        query=ProviderQuery(
            subject_id=subject_id,
            identifier_id=identifier_id,
            identifier_kind=IdentifierKind.USERNAME.value,
            identifier_value=normalized_value,
        ),
    )
    return [_github_observation_from_provider(item) for item in result.observations]


async def _keybase_observations(
    normalized_value: str,
    *,
    subject_id,
    identifier_id,
    purpose: Purpose,
    consent_acknowledged: bool,
) -> list[QuickObservation]:
    request = ExecutionRequest(
        provider_name=DEFAULT_KEYBASE_PROVIDER.descriptor.name,
        subject_id=subject_id,
        identifier_id=identifier_id,
        purpose=purpose,
        consent_acknowledged=consent_acknowledged,
    )
    result = await DEFAULT_PROVIDER_RUNTIME.execute(
        request=request,
        query=ProviderQuery(
            subject_id=subject_id,
            identifier_id=identifier_id,
            identifier_kind=IdentifierKind.USERNAME.value,
            identifier_value=normalized_value,
        ),
    )
    return [_keybase_observation_from_provider(item) for item in result.observations]


def _legacy_gitlab_observation(
    payload: dict[str, object],
    *,
    matched_by: str,
) -> QuickObservation | None:
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


async def _gitlab_observations(
    normalized_value: str,
    *,
    identifier_kind: IdentifierKind,
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
        matched_by = "username" if identifier_kind is IdentifierKind.USERNAME else "exact_public_email"
        observation = _legacy_gitlab_observation(payload, matched_by=matched_by)
        return [] if observation is None else [observation]

    request = ExecutionRequest(
        provider_name=DEFAULT_GITLAB_PROVIDER.descriptor.name,
        subject_id=subject_id,
        identifier_id=identifier_id,
        purpose=purpose,
        consent_acknowledged=consent_acknowledged,
    )
    result = await DEFAULT_PROVIDER_RUNTIME.execute(
        request=request,
        query=ProviderQuery(
            subject_id=subject_id,
            identifier_id=identifier_id,
            identifier_kind=identifier_kind.value,
            identifier_value=normalized_value,
        ),
    )
    return [_gitlab_observation_from_provider(item) for item in result.observations]


def _legacy_codeforces_observation(payload: dict[str, object]) -> QuickObservation | None:
    handle = payload.get("handle")
    if not isinstance(handle, str):
        return None
    details = codeforces_public_observation_fields(payload)
    details.update(
        {
            "account_candidate": True,
            "identity_claim": False,
            "field_visibility": "public_profile_api",
            "matched_by": "legacy_injected_lookup",
        }
    )
    return QuickObservation(
        source="codeforces_public_api",
        source_locator=f"https://codeforces.com/profile/{quote(handle, safe='')}",
        summary=f"Codeforces public profile for @{handle}; account candidate only.",
        details=details,
    )


async def _codeforces_observations(
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
        observation = _legacy_codeforces_observation(payload)
        return [] if observation is None else [observation]

    request = ExecutionRequest(
        provider_name=DEFAULT_CODEFORCES_PROVIDER.descriptor.name,
        subject_id=subject_id,
        identifier_id=identifier_id,
        purpose=purpose,
        consent_acknowledged=consent_acknowledged,
    )
    result = await DEFAULT_PROVIDER_RUNTIME.execute(
        request=request,
        query=ProviderQuery(
            subject_id=subject_id,
            identifier_id=identifier_id,
            identifier_kind=IdentifierKind.USERNAME.value,
            identifier_value=normalized_value,
        ),
    )
    return [_codeforces_observation_from_provider(item) for item in result.observations]


async def _bluesky_observations(
    handle: str,
    *,
    subject_id,
    identifier_id,
    purpose: Purpose,
    consent_acknowledged: bool,
) -> list[QuickObservation]:
    request = ExecutionRequest(
        provider_name=DEFAULT_BLUESKY_PROVIDER.descriptor.name,
        subject_id=subject_id,
        identifier_id=identifier_id,
        purpose=purpose,
        consent_acknowledged=consent_acknowledged,
    )
    result = await DEFAULT_PROVIDER_RUNTIME.execute(
        request=request,
        query=ProviderQuery(
            subject_id=subject_id,
            identifier_id=identifier_id,
            identifier_kind=IdentifierKind.USERNAME.value,
            identifier_value=handle,
        ),
    )
    return [_bluesky_observation_from_provider(item) for item in result.observations]


async def _dns_observations(
    normalized_value: str,
    *,
    subject_id,
    identifier_id,
    purpose: Purpose,
    consent_acknowledged: bool,
    injected_lookup: NetworkLookup | None,
) -> list[QuickObservation]:
    if injected_lookup is not None:
        hostname = urlsplit(normalized_value).hostname or ""
        if not hostname:
            return []
        public_ips = await injected_lookup(hostname)
        if not public_ips:
            return []
        return [
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
        ]

    request = ExecutionRequest(
        provider_name=DEFAULT_DNS_PROVIDER.descriptor.name,
        subject_id=subject_id,
        identifier_id=identifier_id,
        purpose=purpose,
        consent_acknowledged=consent_acknowledged,
    )
    result = await DEFAULT_PROVIDER_RUNTIME.execute(
        request=request,
        query=ProviderQuery(
            subject_id=subject_id,
            identifier_id=identifier_id,
            identifier_kind=IdentifierKind.URL.value,
            identifier_value=normalized_value,
        ),
    )
    return [_dns_observation_from_provider(item) for item in result.observations]


async def _wayback_observations(
    normalized_value: str,
    *,
    subject_id,
    identifier_id,
    purpose: Purpose,
    consent_acknowledged: bool,
) -> list[QuickObservation]:
    request = ExecutionRequest(
        provider_name=DEFAULT_WAYBACK_PROVIDER.descriptor.name,
        subject_id=subject_id,
        identifier_id=identifier_id,
        purpose=purpose,
        consent_acknowledged=consent_acknowledged,
    )
    result = await DEFAULT_PROVIDER_RUNTIME.execute(
        request=request,
        query=ProviderQuery(
            subject_id=subject_id,
            identifier_id=identifier_id,
            identifier_kind=IdentifierKind.URL.value,
            identifier_value=normalized_value,
        ),
    )
    return [_wayback_observation_from_provider(item) for item in result.observations]


async def _stack_overflow_observations(
    normalized_value: str,
    *,
    subject_id,
    identifier_id,
    purpose: Purpose,
    consent_acknowledged: bool,
) -> list[QuickObservation]:
    request = ExecutionRequest(
        provider_name=DEFAULT_STACK_OVERFLOW_PROVIDER.descriptor.name,
        subject_id=subject_id,
        identifier_id=identifier_id,
        purpose=purpose,
        consent_acknowledged=consent_acknowledged,
    )
    result = await DEFAULT_PROVIDER_RUNTIME.execute(
        request=request,
        query=ProviderQuery(
            subject_id=subject_id,
            identifier_id=identifier_id,
            identifier_kind=IdentifierKind.URL.value,
            identifier_value=normalized_value,
        ),
    )
    return [_stack_overflow_observation_from_provider(item) for item in result.observations]


async def _openalex_observations(
    normalized_value: str,
    *,
    subject_id,
    identifier_id,
    purpose: Purpose,
    consent_acknowledged: bool,
) -> list[QuickObservation]:
    request = ExecutionRequest(
        provider_name=DEFAULT_OPENALEX_PROVIDER.descriptor.name,
        subject_id=subject_id,
        identifier_id=identifier_id,
        purpose=purpose,
        consent_acknowledged=consent_acknowledged,
    )
    result = await DEFAULT_PROVIDER_RUNTIME.execute(
        request=request,
        query=ProviderQuery(
            subject_id=subject_id,
            identifier_id=identifier_id,
            identifier_kind=IdentifierKind.URL.value,
            identifier_value=normalized_value,
        ),
    )
    return [_openalex_observation_from_provider(item) for item in result.observations]


async def _wikidata_observations(
    normalized_value: str,
    *,
    subject_id,
    identifier_id,
    purpose: Purpose,
    consent_acknowledged: bool,
) -> list[QuickObservation]:
    request = ExecutionRequest(
        provider_name=DEFAULT_WIKIDATA_PROVIDER.descriptor.name,
        subject_id=subject_id,
        identifier_id=identifier_id,
        purpose=purpose,
        consent_acknowledged=consent_acknowledged,
    )
    result = await DEFAULT_PROVIDER_RUNTIME.execute(
        request=request,
        query=ProviderQuery(
            subject_id=subject_id,
            identifier_id=identifier_id,
            identifier_kind=IdentifierKind.URL.value,
            identifier_value=normalized_value,
        ),
    )
    return [_wikidata_observation_from_provider(item) for item in result.observations]


async def _ror_observations(
    normalized_value: str,
    *,
    subject_id,
    identifier_id,
    purpose: Purpose,
    consent_acknowledged: bool,
) -> list[QuickObservation]:
    request = ExecutionRequest(
        provider_name=DEFAULT_ROR_PROVIDER.descriptor.name,
        subject_id=subject_id,
        identifier_id=identifier_id,
        purpose=purpose,
        consent_acknowledged=consent_acknowledged,
    )
    result = await DEFAULT_PROVIDER_RUNTIME.execute(
        request=request,
        query=ProviderQuery(
            subject_id=subject_id,
            identifier_id=identifier_id,
            identifier_kind=IdentifierKind.URL.value,
            identifier_value=normalized_value,
        ),
    )
    return [_ror_observation_from_provider(item) for item in result.observations]


async def _crossref_observations(
    normalized_value: str,
    *,
    subject_id,
    identifier_id,
    purpose: Purpose,
    consent_acknowledged: bool,
) -> list[QuickObservation]:
    request = ExecutionRequest(
        provider_name=DEFAULT_CROSSREF_PROVIDER.descriptor.name,
        subject_id=subject_id,
        identifier_id=identifier_id,
        purpose=purpose,
        consent_acknowledged=consent_acknowledged,
    )
    result = await DEFAULT_PROVIDER_RUNTIME.execute(
        request=request,
        query=ProviderQuery(
            subject_id=subject_id,
            identifier_id=identifier_id,
            identifier_kind=IdentifierKind.URL.value,
            identifier_value=normalized_value,
        ),
    )
    return [_crossref_observation_from_provider(item) for item in result.observations]


async def _datacite_observations(
    normalized_value: str,
    *,
    subject_id,
    identifier_id,
    purpose: Purpose,
    consent_acknowledged: bool,
) -> list[QuickObservation]:
    request = ExecutionRequest(
        provider_name=DEFAULT_DATACITE_PROVIDER.descriptor.name,
        subject_id=subject_id,
        identifier_id=identifier_id,
        purpose=purpose,
        consent_acknowledged=consent_acknowledged,
    )
    result = await DEFAULT_PROVIDER_RUNTIME.execute(
        request=request,
        query=ProviderQuery(
            subject_id=subject_id,
            identifier_id=identifier_id,
            identifier_kind=IdentifierKind.URL.value,
            identifier_value=normalized_value,
        ),
    )
    return [_datacite_observation_from_provider(item) for item in result.observations]


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
    adapter = provider or DEFAULT_SHERLOCK_PROVIDER
    runtime = DEFAULT_PROVIDER_RUNTIME if provider is None else ProviderRuntime(adapters=[adapter])
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
    source_runs = [
        source_result_record(
            source_name="sherlock",
            lead_kind=LeadKind.USERNAME,
            observation_count=len(observations),
        )
    ]
    injected_gitlab = None if gitlab_lookup is lookup_gitlab_username else gitlab_lookup
    injected_codeforces = None if codeforces_lookup is lookup_codeforces_handle else codeforces_lookup
    enrichments = await asyncio.gather(
        _github_observations(
            normalized_value,
            subject_id=subject_id,
            identifier_id=identifier_id,
            purpose=purpose,
            consent_acknowledged=consent_acknowledged,
            injected_lookup=github_lookup,
        ),
        _gitlab_observations(
            normalized_value,
            identifier_kind=IdentifierKind.USERNAME,
            subject_id=subject_id,
            identifier_id=identifier_id,
            purpose=purpose,
            consent_acknowledged=consent_acknowledged,
            injected_lookup=injected_gitlab,
        ),
        _codeforces_observations(
            normalized_value,
            subject_id=subject_id,
            identifier_id=identifier_id,
            purpose=purpose,
            consent_acknowledged=consent_acknowledged,
            injected_lookup=injected_codeforces,
        ),
        return_exceptions=True,
    )
    enrichment_specs = (
        (
            "github_public_api",
            github_lookup is not None,
            enrichments[0],
            "GitHub public profile enrichment was temporarily unavailable.",
        ),
        (
            "gitlab_public_api",
            injected_gitlab is not None,
            enrichments[1],
            "GitLab public profile enrichment was temporarily unavailable.",
        ),
        (
            "codeforces_public_api",
            injected_codeforces is not None,
            enrichments[2],
            "Codeforces public profile enrichment was temporarily unavailable.",
        ),
    )
    for source_name, injected_attempt, outcome, warning in enrichment_specs:
        if isinstance(outcome, BaseException):
            warnings.append(warning)
            source_run = _source_run_for_exception(
                source_name=source_name,
                lead_kind=LeadKind.USERNAME,
                exc=outcome,
                injected_attempt=injected_attempt,
            )
            if source_run is not None:
                source_runs.append(source_run)
            continue
        observations.extend(outcome)
        source_runs.append(
            source_result_record(
                source_name=source_name,
                lead_kind=LeadKind.USERNAME,
                observation_count=len(outcome),
            )
        )

    keybase_username = keybase_username_from_seed(normalized_value)
    if keybase_username is not None:
        try:
            keybase_observations = await _keybase_observations(
                keybase_username,
                subject_id=subject_id,
                identifier_id=identifier_id,
                purpose=purpose,
                consent_acknowledged=consent_acknowledged,
            )
        except Exception as exc:
            keybase_observations = []
            source_run = _source_run_for_exception(
                source_name="keybase_public_user",
                lead_kind=LeadKind.USERNAME,
                exc=exc,
            )
            if source_run is not None:
                source_runs.append(source_run)
            warnings.append("Keybase public account basics were temporarily unavailable.")
        else:
            source_runs.append(
                source_result_record(
                    source_name="keybase_public_user",
                    lead_kind=LeadKind.USERNAME,
                    observation_count=len(keybase_observations),
                )
            )
        observations.extend(keybase_observations)

    try:
        bluesky_handle = normalize_bluesky_handle(normalized_value)
    except BlueskyAdmissionError:
        bluesky_handle = None
    if bluesky_handle is not None:
        try:
            bluesky_observations = await _bluesky_observations(
                bluesky_handle,
                subject_id=subject_id,
                identifier_id=identifier_id,
                purpose=purpose,
                consent_acknowledged=consent_acknowledged,
            )
        except Exception as exc:
            source_run = _source_run_for_exception(
                source_name="bluesky_public_profile",
                lead_kind=LeadKind.USERNAME,
                exc=exc,
            )
            if source_run is not None:
                source_runs.append(source_run)
            if source_run is None or source_run.state is not SourceRunState.WITHHELD:
                warnings.append("Bluesky public profile enrichment was temporarily unavailable.")
        else:
            observations.extend(bluesky_observations)
            source_runs.append(
                source_result_record(
                    source_name="bluesky_public_profile",
                    lead_kind=LeadKind.USERNAME,
                    observation_count=len(bluesky_observations),
                )
            )

    search_observations, search_warning, search_run = await _public_search(
        normalized_value,
        public_search_lookup,
        lead_kind=LeadKind.USERNAME,
        purpose=purpose,
        consent_acknowledged=consent_acknowledged,
    )
    observations.extend(search_observations)
    if search_run is not None:
        source_runs.append(search_run)
    if search_warning:
        warnings.append(search_warning)
    return QuickResearchReport(
        kind=ResearchKind.USERNAME,
        normalized_value=normalized_value,
        observations=tuple(observations),
        warnings=tuple(warnings),
        source_runs=tuple(source_runs),
    )


async def _research_phone(
    normalized_value: str,
    *,
    purpose: Purpose,
    consent_acknowledged: bool,
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
    source_runs = [
        source_result_record(
            source_name="libphonenumber_metadata",
            lead_kind=LeadKind.PHONE,
            observation_count=1,
        )
    ]
    warnings: list[str] = []
    search_observations, search_warning, search_run = await _public_search(
        normalized_value,
        public_search_lookup,
        lead_kind=LeadKind.PHONE,
        purpose=purpose,
        consent_acknowledged=consent_acknowledged,
    )
    observations.extend(search_observations)
    if search_run is not None:
        source_runs.append(search_run)
    if search_warning:
        warnings.append(search_warning)
    return QuickResearchReport(
        kind=ResearchKind.PHONE,
        normalized_value=normalized_value,
        observations=tuple(observations),
        warnings=tuple(warnings),
        source_runs=tuple(source_runs),
    )


async def _research_email(
    normalized_value: str,
    *,
    purpose: Purpose,
    consent_acknowledged: bool,
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
    source_runs = [
        source_result_record(
            source_name="local_normalization",
            lead_kind=LeadKind.EMAIL,
            observation_count=1,
        )
    ]
    warnings: list[str] = []
    subject_id = uuid4()
    identifier_id = uuid4()
    injected_gitlab = None if gitlab_email_lookup is lookup_gitlab_public_email else gitlab_email_lookup
    try:
        gitlab_observations = await _gitlab_observations(
            normalized_value,
            identifier_kind=IdentifierKind.EMAIL,
            subject_id=subject_id,
            identifier_id=identifier_id,
            purpose=purpose,
            consent_acknowledged=consent_acknowledged,
            injected_lookup=injected_gitlab,
        )
    except Exception as exc:
        gitlab_observations = []
        warnings.append("GitLab public-email lookup was temporarily unavailable.")
        source_run = _source_run_for_exception(
            source_name="gitlab_public_api",
            lead_kind=LeadKind.EMAIL,
            exc=exc,
            injected_attempt=injected_gitlab is not None,
        )
        if source_run is not None:
            source_runs.append(source_run)
    else:
        source_runs.append(
            source_result_record(
                source_name="gitlab_public_api",
                lead_kind=LeadKind.EMAIL,
                observation_count=len(gitlab_observations),
            )
        )
    observations.extend(gitlab_observations)
    search_observations, search_warning, search_run = await _public_search(
        normalized_value,
        public_search_lookup,
        lead_kind=LeadKind.EMAIL,
        purpose=purpose,
        consent_acknowledged=consent_acknowledged,
    )
    observations.extend(search_observations)
    if search_run is not None:
        source_runs.append(search_run)
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
        source_runs=tuple(source_runs),
    )


async def _research_url(
    normalized_value: str,
    *,
    purpose: Purpose,
    consent_acknowledged: bool,
    public_search_lookup: PublicSearchLookup = search_exact_public_mentions,
    network_lookup: NetworkLookup = resolve_public_host_ips,
) -> QuickResearchReport:
    parts = urlsplit(normalized_value)
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
    source_runs = [
        source_result_record(
            source_name="local_normalization",
            lead_kind=LeadKind.URL,
            observation_count=1,
        )
    ]
    warnings: list[str] = []
    subject_id = uuid4()
    identifier_id = uuid4()
    injected_network = None if network_lookup is resolve_public_host_ips else network_lookup
    try:
        dns_observations = await _dns_observations(
            normalized_value,
            subject_id=subject_id,
            identifier_id=identifier_id,
            purpose=purpose,
            consent_acknowledged=consent_acknowledged,
            injected_lookup=injected_network,
        )
    except Exception as exc:
        dns_observations = []
        warnings.append("Public DNS infrastructure lookup was temporarily unavailable.")
        source_run = _source_run_for_exception(
            source_name="public_dns_infrastructure",
            lead_kind=LeadKind.URL,
            exc=exc,
            injected_attempt=injected_network is not None,
        )
        if source_run is not None:
            source_runs.append(source_run)
    else:
        source_runs.append(
            source_result_record(
                source_name="public_dns_infrastructure",
                lead_kind=LeadKind.URL,
                observation_count=len(dns_observations),
            )
        )
    observations.extend(dns_observations)

    try:
        wayback_observations = await _wayback_observations(
            normalized_value,
            subject_id=subject_id,
            identifier_id=identifier_id,
            purpose=purpose,
            consent_acknowledged=consent_acknowledged,
        )
    except Exception as exc:
        wayback_observations = []
        warnings.append("Wayback capture availability metadata was temporarily unavailable.")
        source_run = _source_run_for_exception(
            source_name="wayback_url_availability",
            lead_kind=LeadKind.URL,
            exc=exc,
        )
        if source_run is not None:
            source_runs.append(source_run)
    else:
        source_runs.append(
            source_result_record(
                source_name="wayback_url_availability",
                lead_kind=LeadKind.URL,
                observation_count=len(wayback_observations),
            )
        )
    observations.extend(wayback_observations)

    if stack_overflow_user_id_from_url(normalized_value) is not None:
        try:
            stack_overflow_observations = await _stack_overflow_observations(
                normalized_value,
                subject_id=subject_id,
                identifier_id=identifier_id,
                purpose=purpose,
                consent_acknowledged=consent_acknowledged,
            )
        except Exception as exc:
            stack_overflow_observations = []
            warnings.append("Stack Overflow public-profile metadata was temporarily unavailable.")
            source_run = _source_run_for_exception(
                source_name="stack_overflow_public_profile",
                lead_kind=LeadKind.URL,
                exc=exc,
            )
            if source_run is not None:
                source_runs.append(source_run)
        else:
            source_runs.append(
                source_result_record(
                    source_name="stack_overflow_public_profile",
                    lead_kind=LeadKind.URL,
                    observation_count=len(stack_overflow_observations),
                )
            )
        observations.extend(stack_overflow_observations)

    if openalex_author_id_from_url(normalized_value) is not None:
        try:
            openalex_observations = await _openalex_observations(
                normalized_value,
                subject_id=subject_id,
                identifier_id=identifier_id,
                purpose=purpose,
                consent_acknowledged=consent_acknowledged,
            )
        except Exception as exc:
            openalex_observations = []
            source_run = _source_run_for_exception(
                source_name="openalex_exact_author",
                lead_kind=LeadKind.URL,
                exc=exc,
            )
            if source_run is not None:
                source_runs.append(source_run)
            if source_run is None or source_run.reason.value != "credential_not_configured":
                warnings.append("OpenAlex exact-author metadata was temporarily unavailable.")
        else:
            source_runs.append(
                source_result_record(
                    source_name="openalex_exact_author",
                    lead_kind=LeadKind.URL,
                    observation_count=len(openalex_observations),
                )
            )
        observations.extend(openalex_observations)

    if wikidata_entity_id_from_url(normalized_value) is not None:
        try:
            wikidata_observations = await _wikidata_observations(
                normalized_value,
                subject_id=subject_id,
                identifier_id=identifier_id,
                purpose=purpose,
                consent_acknowledged=consent_acknowledged,
            )
        except Exception as exc:
            wikidata_observations = []
            warnings.append("Wikidata exact-entity metadata was temporarily unavailable.")
            source_run = _source_run_for_exception(
                source_name="wikidata_exact_entity",
                lead_kind=LeadKind.URL,
                exc=exc,
            )
            if source_run is not None:
                source_runs.append(source_run)
        else:
            source_runs.append(
                source_result_record(
                    source_name="wikidata_exact_entity",
                    lead_kind=LeadKind.URL,
                    observation_count=len(wikidata_observations),
                )
            )
        observations.extend(wikidata_observations)

    if ror_id_from_url(normalized_value) is not None:
        try:
            ror_observations = await _ror_observations(
                normalized_value,
                subject_id=subject_id,
                identifier_id=identifier_id,
                purpose=purpose,
                consent_acknowledged=consent_acknowledged,
            )
        except Exception as exc:
            ror_observations = []
            warnings.append("ROR exact-organization metadata was temporarily unavailable.")
            source_run = _source_run_for_exception(
                source_name="ror_exact_organization",
                lead_kind=LeadKind.URL,
                exc=exc,
            )
            if source_run is not None:
                source_runs.append(source_run)
        else:
            source_runs.append(
                source_result_record(
                    source_name="ror_exact_organization",
                    lead_kind=LeadKind.URL,
                    observation_count=len(ror_observations),
                )
            )
        observations.extend(ror_observations)

    if crossref_doi_from_url(normalized_value) is not None:
        crossref_completed = False
        try:
            crossref_observations = await _crossref_observations(
                normalized_value,
                subject_id=subject_id,
                identifier_id=identifier_id,
                purpose=purpose,
                consent_acknowledged=consent_acknowledged,
            )
        except Exception as exc:
            crossref_observations = []
            warnings.append("Crossref exact-work metadata was temporarily unavailable.")
            source_run = _source_run_for_exception(
                source_name="crossref_exact_work",
                lead_kind=LeadKind.URL,
                exc=exc,
            )
            if source_run is not None:
                source_runs.append(source_run)
        else:
            crossref_completed = True
            source_runs.append(
                source_result_record(
                    source_name="crossref_exact_work",
                    lead_kind=LeadKind.URL,
                    observation_count=len(crossref_observations),
                )
            )
        observations.extend(crossref_observations)

        if crossref_completed and not crossref_observations:
            try:
                datacite_observations = await _datacite_observations(
                    normalized_value,
                    subject_id=subject_id,
                    identifier_id=identifier_id,
                    purpose=purpose,
                    consent_acknowledged=consent_acknowledged,
                )
            except Exception as exc:
                datacite_observations = []
                warnings.append("DataCite exact-DOI fallback metadata was temporarily unavailable.")
                source_run = _source_run_for_exception(
                    source_name="datacite_exact_doi",
                    lead_kind=LeadKind.URL,
                    exc=exc,
                )
                if source_run is not None:
                    source_runs.append(source_run)
            else:
                source_runs.append(
                    source_result_record(
                        source_name="datacite_exact_doi",
                        lead_kind=LeadKind.URL,
                        observation_count=len(datacite_observations),
                    )
                )
            observations.extend(datacite_observations)

    search_observations, search_warning, search_run = await _public_search(
        normalized_value,
        public_search_lookup,
        lead_kind=LeadKind.URL,
        purpose=purpose,
        consent_acknowledged=consent_acknowledged,
    )
    observations.extend(search_observations)
    if search_run is not None:
        source_runs.append(search_run)
    if search_warning:
        warnings.append(search_warning)
    return QuickResearchReport(
        kind=ResearchKind.URL,
        normalized_value=normalized_value,
        observations=tuple(observations),
        warnings=tuple(warnings),
        source_runs=tuple(source_runs),
    )


async def _research_domain(
    normalized_value: str,
    *,
    purpose: Purpose,
    consent_acknowledged: bool,
) -> QuickResearchReport:
    """Run explicit DOMAIN research through the metadata-only RDAP source."""

    subject_id = uuid4()
    identifier_id = uuid4()
    request = ExecutionRequest(
        provider_name=DEFAULT_RDAP_PROVIDER.descriptor.name,
        subject_id=subject_id,
        identifier_id=identifier_id,
        purpose=purpose,
        consent_acknowledged=consent_acknowledged,
    )
    try:
        result = await DEFAULT_PROVIDER_RUNTIME.execute(
            request=request,
            query=ProviderQuery(
                subject_id=subject_id,
                identifier_id=identifier_id,
                identifier_kind=IdentifierKind.DOMAIN.value,
                identifier_value=normalized_value,
            ),
        )
    except Exception as exc:
        source_run = _source_run_for_exception(
            source_name="rdap_domain_registry",
            lead_kind=LeadKind.DOMAIN,
            exc=exc,
        )
        warnings = ("Authoritative RDAP domain metadata was unavailable.",)
        return QuickResearchReport(
            kind=ResearchKind.DOMAIN,
            normalized_value=normalized_value,
            observations=(),
            warnings=warnings,
            source_runs=() if source_run is None else (source_run,),
        )

    observations = tuple(_rdap_observation_from_provider(item) for item in result.observations)
    return QuickResearchReport(
        kind=ResearchKind.DOMAIN,
        normalized_value=normalized_value,
        observations=observations,
        warnings=(),
        source_runs=(
            source_result_record(
                source_name="rdap_domain_registry",
                lead_kind=LeadKind.DOMAIN,
                observation_count=len(observations),
            ),
        ),
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
            purpose=purpose,
            consent_acknowledged=consent_acknowledged,
            public_search_lookup=public_search_lookup,
        )
    if kind is ResearchKind.EMAIL:
        return await _research_email(
            normalized.normalized_value,
            purpose=purpose,
            consent_acknowledged=consent_acknowledged,
            gitlab_email_lookup=gitlab_email_lookup,
            public_search_lookup=public_search_lookup,
        )
    if kind is ResearchKind.URL:
        return await _research_url(
            normalized.normalized_value,
            purpose=purpose,
            consent_acknowledged=consent_acknowledged,
            public_search_lookup=public_search_lookup,
            network_lookup=network_lookup,
        )
    if kind is ResearchKind.DOMAIN:
        return await _research_domain(
            normalized.normalized_value,
            purpose=purpose,
            consent_acknowledged=consent_acknowledged,
        )
    raise ValueError("Unsupported research kind.")