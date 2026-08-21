# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from uuid import uuid4

import pytest

from app.intelligence.contracts import LeadKind
from app.intelligence.source_bindings import SOURCE_BINDING_BY_NAME, SourceBindingError, source_binding_for
from app.intelligence.source_catalog import SOURCE_BY_NAME, SourceStatus
from app.intelligence.source_outcomes import source_provider_exception_record
from app.intelligence.source_states import SourceRunReason, SourceRunState
from app.models import Purpose
from app.providers.base import ProviderQuery, ProviderStatus
from app.providers.codeforces_public import CodeforcesPublicProfileProvider
from app.providers.contracts import ExecutionRequest
from app.providers.errors import ProviderPolicyError
from app.providers.registry import PROVIDER_BY_NAME
from app.providers.runtime import ProviderRuntime


def test_codeforces_is_review_required_and_has_no_executable_binding() -> None:
    source = SOURCE_BY_NAME["codeforces_public_api"]
    assert source.status is SourceStatus.REVIEW_REQUIRED
    assert source.source_policy_reviewed is False
    assert source.recursive_eligible is False
    assert "codeforces_public_api" not in SOURCE_BINDING_BY_NAME

    descriptor = PROVIDER_BY_NAME["codeforces_public_api"]
    assert descriptor.status == ProviderStatus.REVIEW_REQUIRED.value

    with pytest.raises(SourceBindingError, match="no executable runtime binding"):
        source_binding_for("codeforces_public_api", kind=LeadKind.USERNAME)


@pytest.mark.asyncio
async def test_codeforces_runtime_rejects_before_provider_contact_and_reports_policy_non_attempt() -> None:
    contacted = False

    async def forbidden_fetcher(_handle: str):
        nonlocal contacted
        contacted = True
        return {"handle": "tourist"}

    provider = CodeforcesPublicProfileProvider(fetcher=forbidden_fetcher)
    runtime = ProviderRuntime(adapters=[provider])
    subject_id = uuid4()
    identifier_id = uuid4()
    request = ExecutionRequest(
        provider_name="codeforces_public_api",
        subject_id=subject_id,
        identifier_id=identifier_id,
        purpose=Purpose.PUBLIC_SOURCE_RESEARCH,
        consent_acknowledged=True,
    )

    with pytest.raises(ProviderPolicyError) as exc_info:
        await runtime.execute(
            request=request,
            query=ProviderQuery(
                subject_id=subject_id,
                identifier_id=identifier_id,
                identifier_kind="username",
                identifier_value="tourist",
            ),
        )

    assert contacted is False
    source_run = source_provider_exception_record(
        source_name="codeforces_public_api",
        lead_kind=LeadKind.USERNAME,
        exc=exc_info.value,
    )
    assert source_run is not None
    assert source_run.state is SourceRunState.BLOCKED
    assert source_run.reason is SourceRunReason.PROVIDER_POLICY
    assert source_run.execution_attempted is False
    assert source_run.observation_count == 0
