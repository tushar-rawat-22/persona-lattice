# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from app.intelligence.source_bindings import SOURCE_BINDING_BY_NAME, SourceExecutionBackend
from app.intelligence.source_catalog import SOURCE_BY_NAME, SourceStatus
from app.providers.base import ProviderStatus
from app.providers.registry import PROVIDER_BY_NAME
from app.providers.shared_runtime import DEFAULT_PROVIDER_RUNTIME


def _governed_provider_names() -> set[str]:
    return {
        binding.provider_name
        for binding in SOURCE_BINDING_BY_NAME.values()
        if binding.backend is SourceExecutionBackend.M3_GOVERNED_ADAPTER
        and binding.provider_name is not None
    }


def test_governed_bindings_have_exactly_one_process_runtime_owner() -> None:
    governed_bindings = {
        name: binding
        for name, binding in SOURCE_BINDING_BY_NAME.items()
        if binding.backend is SourceExecutionBackend.M3_GOVERNED_ADAPTER
    }
    provider_names = [binding.provider_name for binding in governed_bindings.values()]

    assert all(provider_names)
    assert len(provider_names) == len(set(provider_names))
    assert set(DEFAULT_PROVIDER_RUNTIME.adapters) == set(provider_names)

    for source_name, binding in governed_bindings.items():
        assert binding.provider_name is not None
        adapter = DEFAULT_PROVIDER_RUNTIME.adapters[binding.provider_name]
        assert adapter.descriptor is PROVIDER_BY_NAME[binding.provider_name]

        capability = SOURCE_BY_NAME[source_name]
        assert capability.status in {SourceStatus.ACTIVE, SourceStatus.OPTIONAL}
        assert capability.source_policy_reviewed is True
        assert capability.recursive_eligible is True


def test_every_development_provider_has_a_current_governed_runtime_owner() -> None:
    development_provider_names = {
        name
        for name, descriptor in PROVIDER_BY_NAME.items()
        if descriptor.status == ProviderStatus.DEVELOPMENT.value
    }

    assert development_provider_names == _governed_provider_names()
    assert development_provider_names == set(DEFAULT_PROVIDER_RUNTIME.adapters)


def test_zero_spend_baseline_never_depends_on_a_nonzero_spend_active_source() -> None:
    current_recursive_sources = {
        source.name: source
        for source in SOURCE_BY_NAME.values()
        if source.status in {SourceStatus.ACTIVE, SourceStatus.OPTIONAL}
        and source.source_policy_reviewed
        and source.recursive_eligible
    }

    for source in current_recursive_sources.values():
        if source.status is SourceStatus.ACTIVE:
            assert source.zero_spend_eligible is True
        if not source.zero_spend_eligible:
            assert source.status is SourceStatus.OPTIONAL


def test_runtime_cannot_silently_activate_a_planned_or_unreviewed_source() -> None:
    runtime_provider_names = set(DEFAULT_PROVIDER_RUNTIME.adapters)

    for source_name, source in SOURCE_BY_NAME.items():
        if source_name not in runtime_provider_names:
            continue
        assert source.status in {SourceStatus.ACTIVE, SourceStatus.OPTIONAL}
        assert source.source_policy_reviewed is True
        assert source.recursive_eligible is True
        assert source_name in SOURCE_BINDING_BY_NAME
