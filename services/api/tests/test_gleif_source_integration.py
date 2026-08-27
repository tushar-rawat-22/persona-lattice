# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from app.intelligence.contracts import LeadKind
from app.intelligence.source_bindings import SOURCE_BINDING_BY_NAME, validate_source_bindings
from app.intelligence.source_catalog import SOURCE_BY_NAME, SourceCostClass, SourceCredentialClass, SourceStatus
from app.intelligence.source_planner import build_source_plan
from app.providers.base import ContactRisk, ProviderStatus
from app.providers.registry import PROVIDER_BY_NAME
from app.providers.shared_runtime import DEFAULT_GLEIF_PROVIDER, DEFAULT_PROVIDER_RUNTIME


def test_gleif_source_policy_runtime_and_planner_are_aligned() -> None:
    source = SOURCE_BY_NAME["gleif_exact_lei"]
    assert source.status is SourceStatus.ACTIVE
    assert source.cost_class is SourceCostClass.ZERO_DIRECT_COST
    assert source.credential_class is SourceCredentialClass.NONE
    assert source.source_policy_reviewed is True
    assert source.recursive_eligible is True
    assert source.emits == frozenset()

    descriptor = PROVIDER_BY_NAME["gleif_exact_lei"]
    assert descriptor.status == ProviderStatus.DEVELOPMENT.value
    assert descriptor.contact_risk is ContactRisk.NONE_KNOWN
    assert descriptor.supported_identifier_kinds == frozenset({"url"})

    binding = SOURCE_BINDING_BY_NAME["gleif_exact_lei"]
    assert binding.provider_name == "gleif_exact_lei"
    assert binding.accepts == frozenset({LeadKind.URL})

    assert DEFAULT_GLEIF_PROVIDER.descriptor is descriptor
    assert DEFAULT_PROVIDER_RUNTIME.adapters["gleif_exact_lei"] is DEFAULT_GLEIF_PROVIDER

    validate_source_bindings()
    plan = build_source_plan(LeadKind.URL, zero_spend_only=True)
    assert "gleif_exact_lei" in {item.name for item in plan.active}
