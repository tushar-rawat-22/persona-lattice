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
            "Official unauthenticated GitHub user-profile endpoint; only explicitly public "
            "profile fields are admitted and the result remains an account candidate."
        ),
        version="rest-2026-03-10",
        source_category=SourceCategory.PUBLIC_WEB,
        allowed_purposes=SAFE_PURPOSES,
        supported_identifier_kinds=USERNAME_ONLY,
        max_attempts=1,
        timeout_seconds=4.0,
        max_response_bytes=64 * 1024,
        max_concurrency=2,
        rate_limit=50,
        rate_window_seconds=3600.0,
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
