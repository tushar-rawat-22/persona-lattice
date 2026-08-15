# SPDX-License-Identifier: Apache-2.0
from uuid import uuid4

import pytest

from app.models import Purpose
from app.providers import (
    ContactRisk,
    ExecutionRequest,
    ProviderDescriptor,
    ProviderPolicyError,
    ProviderStatus,
    QueryOrigin,
    SourceCategory,
    authorize_execution,
)
from app.uploads import (
    CandidateOrigin,
    CandidateType,
    ReviewCandidate,
    ReviewStatus,
)


SAFE = frozenset({Purpose.SELF_AUDIT, Purpose.PUBLIC_SOURCE_RESEARCH})


def _descriptor(**overrides) -> ProviderDescriptor:
    values = {
        "name": "synthetic_policy",
        "capability": "test",
        "status": ProviderStatus.SYNTHETIC.value,
        "contact_risk": ContactRisk.NONE_KNOWN,
        "reason": "synthetic",
        "version": "1",
        "source_category": SourceCategory.SYNTHETIC,
        "allowed_purposes": SAFE,
    }
    values.update(overrides)
    return ProviderDescriptor(**values)


def _request(**overrides) -> ExecutionRequest:
    values = {
        "provider_name": "synthetic_policy",
        "subject_id": uuid4(),
        "identifier_id": uuid4(),
        "purpose": Purpose.SELF_AUDIT,
        "consent_acknowledged": True,
    }
    values.update(overrides)
    return ExecutionRequest(**values)


def test_policy_blocks_unapproved_provider_and_missing_consent() -> None:
    with pytest.raises(ProviderPolicyError):
        authorize_execution(_descriptor(status=ProviderStatus.PLANNED.value), _request())

    with pytest.raises(ProviderPolicyError):
        authorize_execution(_descriptor(), _request(consent_acknowledged=False))


def test_policy_blocks_regulated_and_contact_risk_execution() -> None:
    regulated = _descriptor(allowed_purposes=frozenset({Purpose.EMPLOYMENT_DECISION}))
    with pytest.raises(ProviderPolicyError):
        authorize_execution(
            regulated,
            _request(purpose=Purpose.EMPLOYMENT_DECISION),
        )

    risky = _descriptor(contact_risk=ContactRisk.POSSIBLE)
    with pytest.raises(ProviderPolicyError):
        authorize_execution(risky, _request(silent_mode=True))


def test_document_candidate_requires_confirmed_research_authority() -> None:
    pending = ReviewCandidate(
        candidate_id=uuid4(),
        candidate_type=CandidateType.IDENTIFIER,
        origin=CandidateOrigin.RULE,
        source_artifact_id=uuid4(),
        value="person@example.test",
        review_status=ReviewStatus.PENDING,
        external_research_authorized=False,
    )
    request = _request(
        query_origin=QueryOrigin.CONFIRMED_DOCUMENT_CANDIDATE,
        document_candidate=pending,
    )
    with pytest.raises(ProviderPolicyError):
        authorize_execution(_descriptor(), request)
