# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import pytest

from app.intelligence.contracts import LeadKind
from app.intelligence.source_bindings import (
    SOURCE_BINDING_BY_NAME,
    SourceBindingError,
    SourceExecutionBackend,
    source_binding_for,
    validate_source_bindings,
)
from app.intelligence.source_catalog import SOURCE_BY_NAME, SourceStatus
from app.providers.base import ContactRisk, ProviderStatus
from app.providers.registry import PROVIDER_BY_NAME


def test_every_current_recursive_source_has_exactly_one_runtime_owner() -> None:
    validate_source_bindings()
    required = {
        source.name
        for source in SOURCE_BY_NAME.values()
        if source.status in {SourceStatus.ACTIVE, SourceStatus.OPTIONAL}
        and source.source_policy_reviewed
        and source.recursive_eligible
    }
    assert set(SOURCE_BINDING_BY_NAME) == required


def test_every_binding_kind_is_declared_by_its_source_capability() -> None:
    for name, binding in SOURCE_BINDING_BY_NAME.items():
        assert binding.accepts
        assert binding.accepts.issubset(SOURCE_BY_NAME[name].accepts)


def test_only_deterministic_no_network_sources_use_local_backend() -> None:
    local = {
        name
        for name, binding in SOURCE_BINDING_BY_NAME.items()
        if binding.backend is SourceExecutionBackend.LOCAL_DETERMINISTIC
    }
    assert local == {"local_normalization", "libphonenumber_metadata"}


def test_no_current_source_uses_legacy_research_execution() -> None:
    legacy = {
        name
        for name, binding in SOURCE_BINDING_BY_NAME.items()
        if binding.backend is SourceExecutionBackend.LEGACY_RESEARCH
    }
    assert legacy == set()


@pytest.mark.parametrize(
    "name",
    ["sherlock"],
)
def test_username_only_governed_sources_match_provider_descriptors(name: str) -> None:
    binding = source_binding_for(name, kind=LeadKind.USERNAME)
    descriptor = PROVIDER_BY_NAME[name]
    assert binding.backend is SourceExecutionBackend.M3_GOVERNED_ADAPTER
    assert binding.provider_name == name
    assert descriptor.status == ProviderStatus.DEVELOPMENT.value
    assert descriptor.contact_risk is ContactRisk.NONE_KNOWN
    assert descriptor.supported_identifier_kinds == frozenset({"username"})


def test_bluesky_username_and_url_binding_matches_provider_descriptor() -> None:
    binding = source_binding_for("bluesky_public_profile", kind=LeadKind.URL)
    descriptor = PROVIDER_BY_NAME["bluesky_public_profile"]
    assert binding.backend is SourceExecutionBackend.M3_GOVERNED_ADAPTER
    assert binding.provider_name == "bluesky_public_profile"
    assert binding.accepts == frozenset({LeadKind.USERNAME, LeadKind.URL})
    assert descriptor.status == ProviderStatus.DEVELOPMENT.value
    assert descriptor.contact_risk is ContactRisk.NONE_KNOWN
    assert descriptor.supported_identifier_kinds == frozenset({"username", "url"})


def test_github_governed_binding_shares_one_provider_for_username_and_exact_repository_url() -> None:
    descriptor = PROVIDER_BY_NAME["github_public_api"]
    for kind in (LeadKind.USERNAME, LeadKind.URL):
        binding = source_binding_for("github_public_api", kind=kind)
        assert binding.backend is SourceExecutionBackend.M3_GOVERNED_ADAPTER
        assert binding.provider_name == "github_public_api"
    assert descriptor.status == ProviderStatus.DEVELOPMENT.value
    assert descriptor.contact_risk is ContactRisk.NONE_KNOWN
    assert descriptor.supported_identifier_kinds == frozenset({"username", "url"})
    assert descriptor.max_attempts == 1
    assert descriptor.timeout_seconds == 4.0
    assert descriptor.max_response_bytes == 64 * 1024
    assert descriptor.max_concurrency == 2
    assert descriptor.rate_limit == 50
    assert descriptor.rate_window_seconds == 3600.0


def test_gitlab_governed_binding_shares_one_provider_for_profiles_email_and_project_urls() -> None:
    descriptor = PROVIDER_BY_NAME["gitlab_public_api"]
    for kind in (LeadKind.USERNAME, LeadKind.EMAIL, LeadKind.URL):
        binding = source_binding_for("gitlab_public_api", kind=kind)
        assert binding.backend is SourceExecutionBackend.M3_GOVERNED_ADAPTER
        assert binding.provider_name == "gitlab_public_api"
    assert descriptor.status == ProviderStatus.DEVELOPMENT.value
    assert descriptor.contact_risk is ContactRisk.NONE_KNOWN
    assert descriptor.supported_identifier_kinds == frozenset({"username", "email", "url"})
    assert descriptor.max_attempts == 1
    assert descriptor.timeout_seconds == 4.0
    assert descriptor.max_response_bytes == 64 * 1024
    assert descriptor.max_concurrency == 2
    assert descriptor.rate_limit == 20
    assert descriptor.rate_window_seconds == 60.0


def test_public_dns_is_governed_for_url_only_and_never_domain_seed_today() -> None:
    capability = SOURCE_BY_NAME["public_dns_infrastructure"]
    descriptor = PROVIDER_BY_NAME["public_dns_infrastructure"]
    binding = source_binding_for("public_dns_infrastructure", kind=LeadKind.URL)

    assert capability.accepts == frozenset({LeadKind.URL, LeadKind.DOMAIN})
    assert binding.accepts == frozenset({LeadKind.URL})
    assert binding.backend is SourceExecutionBackend.M3_GOVERNED_ADAPTER
    assert binding.provider_name == "public_dns_infrastructure"
    assert descriptor.status == ProviderStatus.DEVELOPMENT.value
    assert descriptor.contact_risk is ContactRisk.NONE_KNOWN
    assert descriptor.supported_identifier_kinds == frozenset({"url"})

    with pytest.raises(SourceBindingError, match="not currently bound"):
        source_binding_for("public_dns_infrastructure", kind=LeadKind.DOMAIN)


def test_wayback_governed_binding_is_metadata_only_url_execution() -> None:
    capability = SOURCE_BY_NAME["wayback_url_availability"]
    descriptor = PROVIDER_BY_NAME["wayback_url_availability"]
    binding = source_binding_for("wayback_url_availability", kind=LeadKind.URL)

    assert capability.status is SourceStatus.ACTIVE
    assert capability.accepts == frozenset({LeadKind.URL})
    assert capability.emits == frozenset()
    assert capability.source_policy_reviewed is True
    assert capability.zero_spend_eligible is True
    assert binding.backend is SourceExecutionBackend.M3_GOVERNED_ADAPTER
    assert binding.provider_name == "wayback_url_availability"
    assert descriptor.status == ProviderStatus.DEVELOPMENT.value
    assert descriptor.contact_risk is ContactRisk.NONE_KNOWN
    assert descriptor.supported_identifier_kinds == frozenset({"url"})


def test_rdap_governed_binding_is_metadata_only_domain_execution() -> None:
    capability = SOURCE_BY_NAME["rdap_domain_registry"]
    descriptor = PROVIDER_BY_NAME["rdap_domain_registry"]
    binding = source_binding_for("rdap_domain_registry", kind=LeadKind.DOMAIN)

    assert capability.status is SourceStatus.ACTIVE
    assert capability.accepts == frozenset({LeadKind.DOMAIN})
    assert capability.emits == frozenset()
    assert capability.source_policy_reviewed is True
    assert binding.backend is SourceExecutionBackend.M3_GOVERNED_ADAPTER
    assert binding.provider_name == "rdap_domain_registry"
    assert binding.accepts == frozenset({LeadKind.DOMAIN})
    assert descriptor.status == ProviderStatus.DEVELOPMENT.value
    assert descriptor.contact_risk is ContactRisk.NONE_KNOWN
    assert descriptor.supported_identifier_kinds == frozenset({"domain"})


def test_webfinger_planning_is_url_only_and_does_not_claim_activitypub_fields() -> None:
    capability = SOURCE_BY_NAME["webfinger_activitypub"]
    assert capability.status is SourceStatus.PLANNED
    assert capability.accepts == frozenset({LeadKind.URL})
    assert capability.emits == frozenset({LeadKind.URL})
    assert capability.source_policy_reviewed is False
    assert capability.recursive_eligible is False


def test_planned_and_deferred_sources_have_no_executable_binding() -> None:
    for name in (
        "codeforces_public_api",
        "gravatar_public_profile",
        "webfinger_activitypub",
        "google_people_authorized",
        "numverify",
        "abstract_phone_intelligence",
        "ipqualityscore",
        "maigret",
        "whatsmyname",
        "truecaller_manual",
        "phoneinfoga",
    ):
        with pytest.raises(SourceBindingError, match="no executable runtime binding"):
            source_binding_for(name)


def test_binding_lookup_rejects_wrong_lead_kind() -> None:
    with pytest.raises(SourceBindingError, match="not currently bound"):
        source_binding_for("github_public_api", kind=LeadKind.EMAIL)


def test_optional_metered_search_is_governed_but_not_zero_spend() -> None:
    capability = SOURCE_BY_NAME["brave_public_web_index"]
    for kind in (LeadKind.USERNAME, LeadKind.EMAIL, LeadKind.PHONE, LeadKind.URL):
        binding = source_binding_for("brave_public_web_index", kind=kind)
        assert binding.backend is SourceExecutionBackend.M3_GOVERNED_ADAPTER
        assert binding.provider_name == "brave_public_web_index"
    assert capability.status is SourceStatus.OPTIONAL
    assert capability.zero_spend_eligible is False
