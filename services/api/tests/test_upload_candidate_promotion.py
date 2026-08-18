# SPDX-License-Identifier: Apache-2.0
from uuid import uuid4

import pytest

from app.evidence import IdentifierKind
from app.intelligence import LeadDisposition, LeadKind, LeadReason
from app.uploads import (
    CandidateReviewError,
    CandidateType,
    ReviewCandidate,
    ReviewStatus,
    confirm_candidate,
    extract_identifier_candidates,
    make_claim_candidate,
    promote_confirmed_identifier_candidate,
    reject_candidate,
)


def test_extracted_identifier_preserves_character_span() -> None:
    artifact_id = uuid4()
    text = "Resume contact: Person@Example.TEST; portfolio follows."

    candidate = extract_identifier_candidates(text, artifact_id)[0]

    assert candidate.value == "Person@example.test"
    assert candidate.source_start is not None
    assert candidate.source_end is not None
    assert text[candidate.source_start:candidate.source_end] == "Person@Example.TEST"
    assert candidate.source_page is None


def test_only_confirmed_authorized_identifier_becomes_auto_pivot_lead() -> None:
    artifact_id = uuid4()
    candidate = extract_identifier_candidates("Handle: @CaseHandle", artifact_id)[0]

    with pytest.raises(CandidateReviewError, match="not authorized"):
        promote_confirmed_identifier_candidate(candidate)

    confirmed = confirm_candidate(candidate, human_confirmed=True)
    lead = promote_confirmed_identifier_candidate(confirmed)

    assert lead.kind is LeadKind.USERNAME
    assert lead.value == "CaseHandle"
    assert lead.comparison_key == "CaseHandle"
    assert lead.disposition is LeadDisposition.AUTO_PIVOT
    assert lead.reason is LeadReason.REVIEWED_DOCUMENT_IDENTIFIER
    assert lead.source == "reviewed_upload_candidate"
    assert lead.field_name == IdentifierKind.USERNAME.value
    assert str(artifact_id) in lead.source_locator
    assert str(candidate.candidate_id) in lead.source_locator
    assert f"offset={candidate.source_start}-{candidate.source_end}" in lead.source_locator


def test_claim_candidate_never_becomes_research_lead_even_after_review() -> None:
    claim = make_claim_candidate(
        artifact_id=uuid4(),
        statement="The subject may work at Example Co.",
    )
    confirmed = confirm_candidate(claim, human_confirmed=True)

    assert confirmed.candidate_type is CandidateType.CLAIM
    assert confirmed.external_research_authorized is False
    with pytest.raises(CandidateReviewError, match="not authorized"):
        promote_confirmed_identifier_candidate(confirmed)


def test_rejected_candidate_requires_an_explicit_new_review_before_promotion() -> None:
    candidate = extract_identifier_candidates("Email: person@example.test", uuid4())[0]
    rejected = reject_candidate(candidate)

    assert rejected.review_status is ReviewStatus.REJECTED
    assert rejected.external_research_authorized is False
    with pytest.raises(CandidateReviewError, match="not authorized"):
        promote_confirmed_identifier_candidate(rejected)

    reconfirmed = confirm_candidate(rejected, human_confirmed=True)
    lead = promote_confirmed_identifier_candidate(reconfirmed)

    assert reconfirmed.review_status is ReviewStatus.CONFIRMED
    assert reconfirmed.external_research_authorized is True
    assert lead.kind is LeadKind.EMAIL
    assert lead.value == "person@example.test"


def test_non_executable_identifier_kind_fails_closed() -> None:
    candidate = ReviewCandidate(
        candidate_id=uuid4(),
        candidate_type=CandidateType.IDENTIFIER,
        origin="rule",
        source_artifact_id=uuid4(),
        identifier_kind=IdentifierKind.NAME,
        value="Example Person",
        source_start=0,
        source_end=14,
        review_status=ReviewStatus.CONFIRMED,
        external_research_authorized=True,
    )

    with pytest.raises(CandidateReviewError, match="not executable"):
        promote_confirmed_identifier_candidate(candidate)
