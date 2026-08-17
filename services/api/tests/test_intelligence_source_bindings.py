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


def test_current_legacy_network_debt_shrinks_after_codeforces_migration() -> None:
    legacy = {
        name
        for name, binding in SOURCE_BINDING_BY_NAME.items()
        if binding.backend is SourceExecutionBackend.LEGACY_RESEARCH
    }
    assert legacy == {
        "public_dns_infrastructure",
        "brave_public_web_index",
    }
    assert all(SOURCE_BINDING_BY_NAME[name].migration_note.strip() for name in legacy)


@pytest.mark.parametrize(
    "name",
    ["sherlock", "github_public_api", "codeforces_public_api"],
)
def test_username_only_governed_sources_match_provider_descriptors(name: str) -> None:
    binding = source_binding_for(name, kind=LeadKind.USERNAME)
    descriptor = PROVIDER_BY_NAME[name]
    assert binding.backend is SourceExecutionBackend.M3_GOVERNED_ADAPTER
    assert binding.provider_name == name
    assert descriptor.status == ProviderStatus.DEVELOPMENT.value
    assert descriptor.contact_risk is ContactRisk.NONE_KNOWN
    assert descriptor.supported_identifier_kinds == frozenset({"username"})


def test_gitlab_governed_binding_supports_username_and_exact_public_email() -> None:
    descriptor = PROVIDER_BY_NAME["gitlab_public_api"]
    for kind in (LeadKind.USERNAME, LeadKind.EMAIL):
        binding = source_binding_for("gitlab_public_api", kind=kind)
        assert binding.backend is SourceExecutionBackend.M3_GOVERNED_ADAPTER
        assert binding.provider_name == "gitlab_public_api"
    assert descriptor.status == ProviderStatus.DEVELOPMENT.value
    assert descriptor.contact_risk is ContactRisk.NONE_KNOWN
    assert descriptor.supported_identifier_kinds == frozenset({"username", "email"})


def test_planned_and_deferred_sources_have_no_executable_binding() -> None:
    for name in (
        "bluesky_public_profile",
        "gravatar_public_profile",
        "webfinger_activitypub",
        "rdap_domain_registry",
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


def test_public_dns_is_network_migration_debt_and_only_url_is_wired_today() -> None:
    capability = SOURCE_BY_NAME["public_dns_infrastructure"]
    binding = source_binding_for("public_dns_infrastructure", kind=LeadKind.URL)
    assert capability.accepts == frozenset({LeadKind.URL, LeadKind.DOMAIN})
    assert binding.accepts == frozenset({LeadKind.URL})
    assert binding.backend is SourceExecutionBackend.LEGACY_RESEARCH
    assert "network" in binding.migration_note.casefold()
    with pytest.raises(SourceBindingError, match="not currently bound"):
        source_binding_for("public_dns_infrastructure", kind=LeadKind.DOMAIN)


def test_optional_metered_search_has_binding_but_stays_optional_in_catalog() -> None:
    binding = source_binding_for("brave_public_web_index", kind=LeadKind.EMAIL)
    capability = SOURCE_BY_NAME["brave_public_web_index"]
    assert binding.backend is SourceExecutionBackend.LEGACY_RESEARCH
    assert capability.status is SourceStatus.OPTIONAL
    assert capability.zero_spend_eligible is False
