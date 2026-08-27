# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from app.intelligence.contracts import LeadKind
from app.intelligence.source_bindings import SOURCE_BINDING_BY_NAME, SourceExecutionBackend
from app.intelligence.source_catalog import SOURCE_BY_NAME, SourceStatus
from app.providers.base import ContactRisk, ProviderStatus, SourceCategory
from app.providers.registry import PROVIDER_BY_NAME
from app.providers.shared_runtime import DEFAULT_PROVIDER_RUNTIME


SEC_PROVIDER_NAME = "sec_edgar_exact_cik"


def test_sec_edgar_activation_lands_all_governance_layers_together() -> None:
    descriptor = PROVIDER_BY_NAME[SEC_PROVIDER_NAME]
    source = SOURCE_BY_NAME[SEC_PROVIDER_NAME]
    binding = SOURCE_BINDING_BY_NAME[SEC_PROVIDER_NAME]
    adapter = DEFAULT_PROVIDER_RUNTIME.adapters[SEC_PROVIDER_NAME]

    assert descriptor.status == ProviderStatus.DEVELOPMENT.value
    assert descriptor.contact_risk is ContactRisk.NONE_KNOWN
    assert descriptor.source_category is SourceCategory.REGISTRY
    assert descriptor.supported_identifier_kinds == frozenset({"url"})
    assert descriptor.secret_env is None
    assert descriptor.max_attempts == 1
    assert descriptor.timeout_seconds == 4.0
    assert descriptor.max_response_bytes == 256 * 1024
    assert descriptor.max_concurrency == 1
    assert descriptor.rate_limit == 6
    assert descriptor.rate_window_seconds == 60.0

    assert source.status is SourceStatus.ACTIVE
    assert source.accepts == frozenset({LeadKind.URL})
    assert source.emits == frozenset()
    assert source.zero_spend_eligible is True
    assert source.source_policy_reviewed is True
    assert source.recursive_eligible is True

    assert binding.backend is SourceExecutionBackend.M3_GOVERNED_ADAPTER
    assert binding.provider_name == SEC_PROVIDER_NAME
    assert adapter.descriptor is descriptor
