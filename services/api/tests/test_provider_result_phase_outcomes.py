# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

import pytest

from app.intelligence.contracts import LeadKind
from app.intelligence.source_outcomes import source_provider_exception_record
from app.intelligence.source_states import SourceRunReason, SourceRunState
from app.models import Purpose
from app.providers.base import (
    ContactRisk,
    ProviderDescriptor,
    ProviderObservationData,
    ProviderQuery,
    ProviderResult,
    ProviderStatus,
)
from app.providers.contracts import ExecutionRequest
from app.providers.errors import (
    ProviderAuthError,
    ProviderExecutionError,
    ProviderPolicyError,
    ProviderResultValidationError,
    ProviderValidationError,
)
from app.providers.runtime import ProviderRuntime


_DESCRIPTOR = ProviderDescriptor(
    name="phase_fixture",
    capability="phase_fixture",
    status=ProviderStatus.SYNTHETIC.value,
    contact_risk=ContactRisk.NONE_KNOWN,
    reason="Synthetic provider used to prove execution-phase reporting.",
    allowed_purposes=frozenset({Purpose.PUBLIC_SOURCE_RESEARCH}),
    supported_identifier_kinds=frozenset({"username"}),
)


@dataclass
class _FixtureProvider:
    result: object
    descriptor: ProviderDescriptor = _DESCRIPTOR

    async def execute(self, query: ProviderQuery, secret: str | None):
        return self.result


def _request_and_query() -> tuple[ExecutionRequest, ProviderQuery]:
    subject_id = uuid4()
    identifier_id = uuid4()
    return (
        ExecutionRequest(
            provider_name=_DESCRIPTOR.name,
            subject_id=subject_id,
            identifier_id=identifier_id,
            purpose=Purpose.PUBLIC_SOURCE_RESEARCH,
            consent_acknowledged=False,
        ),
        ProviderQuery(
            subject_id=subject_id,
            identifier_id=identifier_id,
            identifier_kind="username",
            identifier_value="fixture-user",
        ),
    )


@pytest.mark.asyncio
async def test_invalid_result_contract_is_post_attempt_validation() -> None:
    runtime = ProviderRuntime(adapters=[_FixtureProvider(result={"not": "a ProviderResult"})])
    request, query = _request_and_query()

    with pytest.raises(ProviderResultValidationError):
        await runtime.execute(request=request, query=query)


@pytest.mark.asyncio
async def test_non_serializable_payload_is_post_attempt_validation() -> None:
    runtime = ProviderRuntime(
        adapters=[
            _FixtureProvider(
                result=ProviderResult(
                    observations=(
                        ProviderObservationData(
                            source_locator="https://example.test/profile",
                            payload={"bad": object()},
                        ),
                    )
                )
            )
        ]
    )
    request, query = _request_and_query()

    with pytest.raises(ProviderResultValidationError):
        await runtime.execute(request=request, query=query)


@pytest.mark.asyncio
async def test_blank_source_locator_is_post_attempt_validation() -> None:
    runtime = ProviderRuntime(
        adapters=[
            _FixtureProvider(
                result=ProviderResult(
                    observations=(ProviderObservationData(source_locator=" ", payload={}),)
                )
            )
        ]
    )
    request, query = _request_and_query()

    with pytest.raises(ProviderResultValidationError):
        await runtime.execute(request=request, query=query)


def test_provider_exception_mapping_uses_only_provable_phases() -> None:
    policy = source_provider_exception_record(
        source_name="phase_fixture",
        lead_kind=LeadKind.USERNAME,
        exc=ProviderPolicyError("blocked"),
    )
    missing_secret = source_provider_exception_record(
        source_name="phase_fixture",
        lead_kind=LeadKind.USERNAME,
        exc=ProviderAuthError("missing"),
    )
    malformed = source_provider_exception_record(
        source_name="phase_fixture",
        lead_kind=LeadKind.USERNAME,
        exc=ProviderResultValidationError("malformed"),
    )
    execution = source_provider_exception_record(
        source_name="phase_fixture",
        lead_kind=LeadKind.USERNAME,
        exc=ProviderExecutionError("failed"),
    )
    ambiguous_validation = source_provider_exception_record(
        source_name="phase_fixture",
        lead_kind=LeadKind.USERNAME,
        exc=ProviderValidationError("phase unknown"),
    )

    assert policy is not None
    assert policy.state is SourceRunState.BLOCKED
    assert policy.reason is SourceRunReason.PROVIDER_POLICY
    assert policy.execution_attempted is False

    assert missing_secret is not None
    assert missing_secret.state is SourceRunState.UNAVAILABLE
    assert missing_secret.reason is SourceRunReason.CREDENTIAL_NOT_CONFIGURED
    assert missing_secret.execution_attempted is False

    assert malformed is not None
    assert malformed.state is SourceRunState.UNAVAILABLE
    assert malformed.reason is SourceRunReason.MALFORMED_RESULT
    assert malformed.execution_attempted is True

    assert execution is not None
    assert execution.reason is SourceRunReason.EXECUTION_FAILURE
    assert execution.execution_attempted is True

    assert ambiguous_validation is None
