# SPDX-License-Identifier: Apache-2.0
from ..models import Purpose
from .base import (
    AuthMode,
    ContactRisk,
    ProviderDescriptor,
    ProviderStatus,
    SourceCategory,
)


SAFE_PURPOSES = frozenset(
    {
        Purpose.SELF_AUDIT,
        Purpose.CONSENTED_DUE_DILIGENCE,
        Purpose.PUBLIC_SOURCE_RESEARCH,
        Purpose.PROFESSIONAL_VERIFICATION,
    }
)
CONSENTED_PURPOSES = frozenset(
    {
        Purpose.SELF_AUDIT,
        Purpose.CONSENTED_DUE_DILIGENCE,
        Purpose.PROFESSIONAL_VERIFICATION,
    }
)
PHONE_ONLY = frozenset({"phone"})
USERNAME_ONLY = frozenset({"username"})
USERNAME_EMAIL = frozenset({"username", "email"})
USERNAME_URL = frozenset({"username", "url"})
URL_ONLY = frozenset({"url"})
DOMAIN_ONLY = frozenset({"domain"})
PUBLIC_SEARCH_IDENTIFIERS = frozenset({"username", "email", "phone", "url"})


PROVIDERS: tuple[ProviderDescriptor, ...] = (
    ProviderDescriptor(
        name="synthetic_echo",
        capability="framework_verification",
        status=ProviderStatus.SYNTHETIC.value,
        contact_risk=ContactRisk.NONE_KNOWN,
        reason="Synthetic-only adapter used to verify the governed execution boundary.",
        version="1",
        source_category=SourceCategory.SYNTHETIC,
        allowed_purposes=SAFE_PURPOSES,
        max_attempts=3,
        timeout_seconds=1.0,
        max_response_bytes=32 * 1024,
        max_concurrency=2,
        rate_limit=20,
        rate_window_seconds=60.0,
    ),
    ProviderDescriptor(
        name="numverify",
        capability="phone_intelligence",
        status=ProviderStatus.REVIEW_REQUIRED.value,
        contact_risk=ContactRisk.NONE_KNOWN,
        reason="Development adapter only after exact provider-terms/privacy review.",
        source_category=SourceCategory.PHONE_METADATA,
        allowed_purposes=CONSENTED_PURPOSES,
        supported_identifier_kinds=PHONE_ONLY,
        auth_mode=AuthMode.API_KEY,
        secret_env="NUMVERIFY_API_KEY",
    ),
    ProviderDescriptor(
        name="abstract_phone_intelligence",
        capability="phone_intelligence",
        status=ProviderStatus.REVIEW_REQUIRED.value,
        contact_risk=ContactRisk.NONE_KNOWN,
        reason="Development adapter only after exact provider-terms/privacy review.",
        source_category=SourceCategory.PHONE_METADATA,
        allowed_purposes=CONSENTED_PURPOSES,
        supported_identifier_kinds=PHONE_ONLY,
        auth_mode=AuthMode.API_KEY,
        secret_env="ABSTRACT_PHONE_API_KEY",
    ),
    ProviderDescriptor(
        name="ipqualityscore",
        capability="phone_risk",
        status=ProviderStatus.REVIEW_REQUIRED.value,
        contact_risk=ContactRisk.NONE_KNOWN,
        reason="Development adapter only after exact provider-terms/privacy review.",
        source_category=SourceCategory.PHONE_METADATA,
        allowed_purposes=CONSENTED_PURPOSES,
        supported_identifier_kinds=PHONE_ONLY,
        auth_mode=AuthMode.API_KEY,
        secret_env="IPQS_API_KEY",
    ),
    ProviderDescriptor(
        name="maigret",
        capability="username_discovery",
        status=ProviderStatus.PLANNED.value,
        contact_risk=ContactRisk.NONE_KNOWN,
        reason="Reviewed M4 enrichment candidate; recursion/AI/autoupdate/proxies stay disabled.",
        version="0.6.3",
        source_category=SourceCategory.USERNAME_DISCOVERY,
        allowed_purposes=SAFE_PURPOSES,
        supported_identifier_kinds=USERNAME_ONLY,
    ),
    ProviderDescriptor(
        name="sherlock",
        capability="username_discovery",
        status=ProviderStatus.DEVELOPMENT.value,
        contact_risk=ContactRisk.NONE_KNOWN,
        reason="Pinned bounded public-account verifier using only a reviewed packaged site subset.",
        version="0.16.0",
        source_category=SourceCategory.USERNAME_DISCOVERY,
        allowed_purposes=SAFE_PURPOSES,
        supported_identifier_kinds=USERNAME_ONLY,
        max_attempts=1,
        timeout_seconds=8.0,
        max_response_bytes=64 * 1024,
        max_concurrency=1,
        rate_limit=6,
        rate_window_seconds=60.0,
    ),
    ProviderDescriptor(
        name="github_public_api",
        capability="public_profile_enrichment",
        status=ProviderStatus.DEVELOPMENT.value,
        contact_risk=ContactRisk.NONE_KNOWN,
        reason=(
            "Official unauthenticated GitHub user-profile and exact public-repository endpoints; "
            "profile fields remain account-candidate evidence while repository metadata emits no leads."
        ),
        version="rest-2026-03-10",
        source_category=SourceCategory.PUBLIC_WEB,
        allowed_purposes=SAFE_PURPOSES,
        supported_identifier_kinds=USERNAME_URL,
        max_attempts=1,
        timeout_seconds=4.0,
        max_response_bytes=64 * 1024,
        max_concurrency=2,
        rate_limit=50,
        rate_window_seconds=3600.0,
    ),
    ProviderDescriptor(
        name="keybase_public_user",
        capability="public_profile_enrichment",
        status=ProviderStatus.DEVELOPMENT.value,
        contact_risk=ContactRisk.NONE_KNOWN,
        reason=(
            "Official credentialless Keybase username lookup restricted to the public basics object; "
            "same-handle evidence remains an account candidate and no proofs/profile data are requested."
        ),
        version="api-1.0-user-lookup-basics-2026-08",
        source_category=SourceCategory.PUBLIC_WEB,
        allowed_purposes=SAFE_PURPOSES,
        supported_identifier_kinds=USERNAME_ONLY,
        max_attempts=1,
        timeout_seconds=4.0,
        max_response_bytes=16 * 1024,
        max_concurrency=1,
        rate_limit=20,
        rate_window_seconds=60.0,
    ),
    ProviderDescriptor(
        name="gitlab_public_api",
        capability="public_profile_enrichment",
        status=ProviderStatus.DEVELOPMENT.value,
        contact_risk=ContactRisk.NONE_KNOWN,
        reason=(
            "Official unauthenticated GitLab users endpoint; exact username or public-email "
            "matches only, with public profile fields admitted as account-candidate evidence."
        ),
        version="v4",
        source_category=SourceCategory.PUBLIC_WEB,
        allowed_purposes=SAFE_PURPOSES,
        supported_identifier_kinds=USERNAME_EMAIL,
        max_attempts=1,
        timeout_seconds=4.0,
        max_response_bytes=64 * 1024,
        max_concurrency=2,
        rate_limit=20,
        rate_window_seconds=60.0,
    ),
    ProviderDescriptor(
        name="codeforces_public_api",
        capability="public_profile_enrichment",
        status=ProviderStatus.DEVELOPMENT.value,
        contact_risk=ContactRisk.NONE_KNOWN,
        reason=(
            "Official anonymous Codeforces user.info endpoint; public profile fields only, "
            "with exact or historic-handle results retained as account candidates."
        ),
        version="user.info",
        source_category=SourceCategory.PUBLIC_WEB,
        allowed_purposes=SAFE_PURPOSES,
        supported_identifier_kinds=USERNAME_ONLY,
        max_attempts=1,
        timeout_seconds=4.0,
        max_response_bytes=64 * 1024,
        max_concurrency=1,
        rate_limit=1,
        rate_window_seconds=2.0,
    ),
    ProviderDescriptor(
        name="bluesky_public_profile",
        capability="public_profile_enrichment",
        status=ProviderStatus.DEVELOPMENT.value,
        contact_risk=ContactRisk.NONE_KNOWN,
        reason=(
            "Official unauthenticated Bluesky public AppView profile lookup for valid AT handles; "
            "minimal public fields only, with public-web opt-out and unavailable accounts neutral."
        ),
        version="app.bsky.actor.getProfile",
        source_category=SourceCategory.PUBLIC_WEB,
        allowed_purposes=SAFE_PURPOSES,
        supported_identifier_kinds=USERNAME_ONLY,
        max_attempts=1,
        timeout_seconds=4.0,
        max_response_bytes=64 * 1024,
        max_concurrency=2,
        rate_limit=30,
        rate_window_seconds=60.0,
    ),
    ProviderDescriptor(
        name="public_dns_infrastructure",
        capability="public_network_metadata",
        status=ProviderStatus.DEVELOPMENT.value,
        contact_risk=ContactRisk.NONE_KNOWN,
        reason=(
            "System DNS resolution for the hostname of an already-normalized public URL; "
            "globally routable infrastructure addresses only, never subject/device IP evidence."
        ),
        version="system-getaddrinfo-v1",
        source_category=SourceCategory.PUBLIC_WEB,
        allowed_purposes=SAFE_PURPOSES,
        supported_identifier_kinds=URL_ONLY,
        max_attempts=1,
        timeout_seconds=4.0,
        max_response_bytes=16 * 1024,
        max_concurrency=2,
        rate_limit=30,
        rate_window_seconds=60.0,
    ),
    ProviderDescriptor(
        name="wayback_url_availability",
        capability="public_web_archive_metadata",
        status=ProviderStatus.DEVELOPMENT.value,
        contact_risk=ContactRisk.NONE_KNOWN,
        reason=(
            "Official Internet Archive Wayback availability metadata for an already-normalized "
            "public URL; capture metadata only, with no archived page-content retrieval."
        ),
        version="availability-json-v1",
        source_category=SourceCategory.PUBLIC_WEB,
        allowed_purposes=SAFE_PURPOSES,
        supported_identifier_kinds=URL_ONLY,
        max_attempts=1,
        timeout_seconds=4.0,
        max_response_bytes=32 * 1024,
        max_concurrency=1,
        rate_limit=15,
        rate_window_seconds=60.0,
    ),
    ProviderDescriptor(
        name="stack_overflow_public_profile",
        capability="public_profile_enrichment",
        status=ProviderStatus.DEVELOPMENT.value,
        contact_risk=ContactRisk.NONE_KNOWN,
        reason=(
            "Official Stack Exchange API lookup only for an exact numeric Stack Overflow user ID "
            "parsed from a supplied public profile URL; bounded account metadata only."
        ),
        version="api-v2.3-users",
        source_category=SourceCategory.PUBLIC_WEB,
        allowed_purposes=SAFE_PURPOSES,
        supported_identifier_kinds=URL_ONLY,
        max_attempts=1,
        timeout_seconds=4.0,
        max_response_bytes=32 * 1024,
        max_concurrency=1,
        rate_limit=20,
        rate_window_seconds=60.0,
    ),
    ProviderDescriptor(
        name="openalex_exact_author",
        capability="public_scholarly_profile_metadata",
        status=ProviderStatus.DEVELOPMENT.value,
        contact_risk=ContactRisk.NONE_KNOWN,
        reason=(
            "Official OpenAlex singleton author lookup only for an exact supplied OpenAlex author URL; "
            "bounded scholarly-profile metadata with no name search or emitted leads."
        ),
        version="authors-singleton-2026-08",
        source_category=SourceCategory.PUBLIC_WEB,
        allowed_purposes=SAFE_PURPOSES,
        supported_identifier_kinds=URL_ONLY,
        auth_mode=AuthMode.API_KEY,
        secret_env="OPENALEX_API_KEY",
        max_attempts=1,
        timeout_seconds=4.0,
        max_response_bytes=32 * 1024,
        max_concurrency=1,
        rate_limit=20,
        rate_window_seconds=60.0,
    ),
    ProviderDescriptor(
        name="wikidata_exact_entity",
        capability="public_knowledge_entity_metadata",
        status=ProviderStatus.DEVELOPMENT.value,
        contact_risk=ContactRisk.NONE_KNOWN,
        reason=(
            "Official Wikidata wbgetentities lookup only for an exact supplied Wikidata item URL; "
            "English label/description metadata only, with no search, claims expansion or emitted leads."
        ),
        version="wbgetentities-2026-08",
        source_category=SourceCategory.PUBLIC_WEB,
        allowed_purposes=SAFE_PURPOSES,
        supported_identifier_kinds=URL_ONLY,
        max_attempts=1,
        timeout_seconds=4.0,
        max_response_bytes=32 * 1024,
        max_concurrency=1,
        rate_limit=30,
        rate_window_seconds=60.0,
    ),
    ProviderDescriptor(
        name="ror_exact_organization",
        capability="public_organization_registry_metadata",
        status=ProviderStatus.DEVELOPMENT.value,
        contact_risk=ContactRisk.NONE_KNOWN,
        reason=(
            "Official ROR singleton organization lookup only for an exact canonical ROR URL; "
            "bounded CC0 registry metadata with no search, affiliation matching or emitted leads."
        ),
        version="api-v2-single-organization-2026-08",
        source_category=SourceCategory.REGISTRY,
        allowed_purposes=SAFE_PURPOSES,
        supported_identifier_kinds=URL_ONLY,
        max_attempts=1,
        timeout_seconds=4.0,
        max_response_bytes=32 * 1024,
        max_concurrency=1,
        rate_limit=8,
        rate_window_seconds=60.0,
    ),
    ProviderDescriptor(
        name="companies_house_exact_company",
        capability="public_company_registry_metadata",
        status=ProviderStatus.DEVELOPMENT.value,
        contact_risk=ContactRisk.NONE_KNOWN,
        reason=(
            "Official Companies House singleton company-profile lookup only for an exact supplied public "
            "company URL; bounded company metadata with no person, address, filing or search expansion."
        ),
        version="public-data-company-profile-2026-08",
        source_category=SourceCategory.REGISTRY,
        allowed_purposes=SAFE_PURPOSES,
        supported_identifier_kinds=URL_ONLY,
        auth_mode=AuthMode.API_KEY,
        secret_env="COMPANIES_HOUSE_API_KEY",
        max_attempts=1,
        timeout_seconds=4.0,
        max_response_bytes=32 * 1024,
        max_concurrency=1,
        rate_limit=30,
        rate_window_seconds=60.0,
    ),
    ProviderDescriptor(
        name="dblp_exact_person",
        capability="public_scholarly_profile_metadata",
        status=ProviderStatus.DEVELOPMENT.value,
        contact_risk=ContactRisk.NONE_KNOWN,
        reason=(
            "Official DBLP SPARQL lookup only for an exact supplied person PID URL; "
            "bounded CC0 primary-name metadata with no name search, bibliography expansion or emitted leads."
        ),
        version="sparql-primary-creator-name-2026-08",
        source_category=SourceCategory.PUBLIC_WEB,
        allowed_purposes=SAFE_PURPOSES,
        supported_identifier_kinds=URL_ONLY,
        max_attempts=1,
        timeout_seconds=4.0,
        max_response_bytes=32 * 1024,
        max_concurrency=1,
        rate_limit=6,
        rate_window_seconds=60.0,
    ),
    ProviderDescriptor(
        name="crossref_exact_work",
        capability="public_bibliographic_metadata",
        status=ProviderStatus.DEVELOPMENT.value,
        contact_risk=ContactRisk.NONE_KNOWN,
        reason=(
            "Official Crossref singleton work lookup only for an exact supplied doi.org URL; "
            "bounded bibliographic metadata with no search, abstract/full-text expansion or emitted leads."
        ),
        version="rest-single-work-2026-08",
        source_category=SourceCategory.PUBLIC_WEB,
        allowed_purposes=SAFE_PURPOSES,
        supported_identifier_kinds=URL_ONLY,
        max_attempts=1,
        timeout_seconds=4.0,
        max_response_bytes=32 * 1024,
        max_concurrency=1,
        rate_limit=30,
        rate_window_seconds=60.0,
    ),
    ProviderDescriptor(
        name="datacite_exact_doi",
        capability="public_bibliographic_metadata",
        status=ProviderStatus.DEVELOPMENT.value,
        contact_risk=ContactRisk.NONE_KNOWN,
        reason=(
            "Official DataCite singleton DOI lookup used only after an exact Crossref no-match; "
            "bounded CC0 bibliographic metadata with no search, relation expansion or emitted leads."
        ),
        version="rest-single-doi-2026-08",
        source_category=SourceCategory.PUBLIC_WEB,
        allowed_purposes=SAFE_PURPOSES,
        supported_identifier_kinds=URL_ONLY,
        max_attempts=1,
        timeout_seconds=4.0,
        max_response_bytes=32 * 1024,
        max_concurrency=1,
        rate_limit=30,
        rate_window_seconds=60.0,
    ),
    ProviderDescriptor(
        name="brave_public_web_index",
        capability="exact_public_web_search",
        status=ProviderStatus.DEVELOPMENT.value,
        contact_risk=ContactRisk.NONE_KNOWN,
        reason=(
            "Optional metered Brave Web Search path for exact-identifier discovery only; "
            "snippets remain discovery evidence and never become identity claims."
        ),
        version="web-search-v1",
        source_category=SourceCategory.PUBLIC_WEB,
        allowed_purposes=SAFE_PURPOSES,
        supported_identifier_kinds=PUBLIC_SEARCH_IDENTIFIERS,
        auth_mode=AuthMode.API_KEY,
        secret_env="BRAVE_SEARCH_API_KEY",
        max_attempts=1,
        timeout_seconds=5.0,
        max_response_bytes=256 * 1024,
        max_concurrency=1,
        rate_limit=10,
        rate_window_seconds=60.0,
    ),
    ProviderDescriptor(
        name="rdap_domain_registry",
        capability="public_domain_registration_metadata",
        status=ProviderStatus.DEVELOPMENT.value,
        contact_risk=ContactRisk.NONE_KNOWN,
        reason=(
            "IANA-bootstrap-selected authoritative RDAP domain lookup; metadata-only status and "
            "nameserver context, with registration redaction treated as authoritative."
        ),
        version="rfc9082-rfc9224-v1",
        source_category=SourceCategory.REGISTRY,
        allowed_purposes=SAFE_PURPOSES,
        supported_identifier_kinds=DOMAIN_ONLY,
        max_attempts=1,
        timeout_seconds=12.0,
        max_response_bytes=64 * 1024,
        max_concurrency=2,
        rate_limit=10,
        rate_window_seconds=60.0,
    ),
    ProviderDescriptor(
        name="whatsmyname",
        capability="username_dataset",
        status=ProviderStatus.REVIEW_REQUIRED.value,
        contact_risk=ContactRisk.NONE_KNOWN,
        reason="CC BY-SA dataset boundary must be reviewed before any executable use.",
        source_category=SourceCategory.USERNAME_DISCOVERY,
        allowed_purposes=SAFE_PURPOSES,
        supported_identifier_kinds=USERNAME_ONLY,
    ),
    ProviderDescriptor(
        name="truecaller_manual",
        capability="caller_id",
        status=ProviderStatus.MANUAL_ONLY.value,
        contact_risk=ContactRisk.POSSIBLE,
        reason="Excluded from silent automation because lookup visibility/contact risk may exist.",
        source_category=SourceCategory.CALLER_ID,
        allowed_purposes=CONSENTED_PURPOSES,
        supported_identifier_kinds=PHONE_ONLY,
    ),
    ProviderDescriptor(
        name="phoneinfoga",
        capability="phone_osint",
        status=ProviderStatus.REFERENCE_ONLY.value,
        contact_risk=ContactRisk.NONE_KNOWN,
        reason="GPL code is reference-only and not executable through the Apache core.",
        source_category=SourceCategory.REFERENCE,
        allowed_purposes=CONSENTED_PURPOSES,
        supported_identifier_kinds=PHONE_ONLY,
    ),
)

PROVIDER_BY_NAME = {provider.name: provider for provider in PROVIDERS}