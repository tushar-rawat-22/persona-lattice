# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from .admin_auth import require_admin_write
from .audit import AUDIT_STORE
from .authz import AuthenticatedPrincipal
from .evidence import IdentifierKind, InvalidIdentifier
from .intelligence import LeadDisposition, LeadKind, LeadReason
from .models import Purpose
from .providers.errors import (
    ProviderExecutionError,
    ProviderPolicyError,
    ProviderRateBudgetExceeded,
)
from .research import ResearchKind
from .uploads import CandidateReviewError, CandidateType, ReviewCandidate, ReviewStatus
from .uploads.research_service import ReviewedCandidateCaseMode, run_reviewed_candidate_case
from .uploads.review_service import (
    UploadReviewCandidateNotFoundError,
    confirm_stored_candidate,
    promote_stored_candidate,
    reject_stored_candidate,
    reopen_stored_candidate,
)


router = APIRouter(prefix="/v1/files/review", tags=["upload-review"])


class UploadReviewStateResponse(BaseModel):
    artifact_id: UUID
    candidate_id: UUID
    candidate_type: CandidateType
    identifier_kind: IdentifierKind | None
    review_status: ReviewStatus
    external_research_authorized: bool
    source_page: int | None
    source_start: int | None
    source_end: int | None


class PromotedUploadLeadResponse(BaseModel):
    artifact_id: UUID
    candidate_id: UUID
    kind: LeadKind
    value: str
    reason: LeadReason
    disposition: LeadDisposition
    source_locator: str


class ReviewedCandidateCaseRequest(BaseModel):
    mode: ReviewedCandidateCaseMode = ReviewedCandidateCaseMode.CONVERGED
    purpose: Purpose = Purpose.PUBLIC_SOURCE_RESEARCH
    consent_acknowledged: bool = False


class ReviewedCandidateCaseResponse(BaseModel):
    case_id: UUID
    mode: ReviewedCandidateCaseMode
    seed_kind: ResearchKind
    created_at: datetime
    expires_at: datetime


def _state_response(candidate: ReviewCandidate) -> UploadReviewStateResponse:
    return UploadReviewStateResponse(
        artifact_id=candidate.source_artifact_id,
        candidate_id=candidate.candidate_id,
        candidate_type=candidate.candidate_type,
        identifier_kind=candidate.identifier_kind,
        review_status=candidate.review_status,
        external_research_authorized=candidate.external_research_authorized,
        source_page=candidate.source_page,
        source_start=candidate.source_start,
        source_end=candidate.source_end,
    )


def _audit_details(candidate: ReviewCandidate) -> dict[str, object]:
    identifier_kind = (
        candidate.identifier_kind.value if candidate.identifier_kind is not None else None
    )
    return {
        "candidate_type": candidate.candidate_type.value,
        "identifier_kind": identifier_kind,
    }


def _candidate_not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Upload review candidate was not found or has expired.",
    )


@router.post(
    "/{artifact_id}/{candidate_id}/confirm",
    response_model=UploadReviewStateResponse,
)
def confirm_upload_review_candidate(
    artifact_id: UUID,
    candidate_id: UUID,
    _principal: AuthenticatedPrincipal = Depends(require_admin_write),
) -> UploadReviewStateResponse:
    try:
        candidate = confirm_stored_candidate(artifact_id, candidate_id)
    except UploadReviewCandidateNotFoundError as exc:
        raise _candidate_not_found() from exc
    AUDIT_STORE.record("file.review.confirm", details=_audit_details(candidate))
    return _state_response(candidate)


@router.post(
    "/{artifact_id}/{candidate_id}/reject",
    response_model=UploadReviewStateResponse,
)
def reject_upload_review_candidate(
    artifact_id: UUID,
    candidate_id: UUID,
    _principal: AuthenticatedPrincipal = Depends(require_admin_write),
) -> UploadReviewStateResponse:
    try:
        candidate = reject_stored_candidate(artifact_id, candidate_id)
    except UploadReviewCandidateNotFoundError as exc:
        raise _candidate_not_found() from exc
    AUDIT_STORE.record("file.review.reject", details=_audit_details(candidate))
    return _state_response(candidate)


@router.post(
    "/{artifact_id}/{candidate_id}/reopen",
    response_model=UploadReviewStateResponse,
)
def reopen_upload_review_candidate(
    artifact_id: UUID,
    candidate_id: UUID,
    _principal: AuthenticatedPrincipal = Depends(require_admin_write),
) -> UploadReviewStateResponse:
    try:
        candidate = reopen_stored_candidate(artifact_id, candidate_id)
    except UploadReviewCandidateNotFoundError as exc:
        raise _candidate_not_found() from exc
    AUDIT_STORE.record("file.review.reopen", details=_audit_details(candidate))
    return _state_response(candidate)


@router.post(
    "/{artifact_id}/{candidate_id}/promote",
    response_model=PromotedUploadLeadResponse,
)
def promote_upload_review_candidate(
    artifact_id: UUID,
    candidate_id: UUID,
    _principal: AuthenticatedPrincipal = Depends(require_admin_write),
) -> PromotedUploadLeadResponse:
    try:
        lead = promote_stored_candidate(artifact_id, candidate_id)
    except UploadReviewCandidateNotFoundError as exc:
        raise _candidate_not_found() from exc
    except CandidateReviewError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Upload review candidate is not currently authorized for promotion.",
        ) from exc

    AUDIT_STORE.record("file.review.promote", details={"kind": lead.kind.value})
    return PromotedUploadLeadResponse(
        artifact_id=artifact_id,
        candidate_id=candidate_id,
        kind=lead.kind,
        value=lead.value,
        reason=lead.reason,
        disposition=lead.disposition,
        source_locator=lead.source_locator,
    )


@router.post(
    "/{artifact_id}/{candidate_id}/run-case",
    response_model=ReviewedCandidateCaseResponse,
)
async def run_upload_review_candidate_case(
    artifact_id: UUID,
    candidate_id: UUID,
    payload: ReviewedCandidateCaseRequest,
    _principal: AuthenticatedPrincipal = Depends(require_admin_write),
) -> ReviewedCandidateCaseResponse:
    """Explicitly execute a retained case from current server-owned review state."""

    try:
        record = await run_reviewed_candidate_case(
            artifact_id,
            candidate_id,
            mode=payload.mode,
            purpose=payload.purpose,
            consent_acknowledged=payload.consent_acknowledged,
        )
    except UploadReviewCandidateNotFoundError as exc:
        raise _candidate_not_found() from exc
    except CandidateReviewError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Upload review candidate is not currently authorized for research.",
        ) from exc
    except InvalidIdentifier as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    except ProviderPolicyError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Research provider policy blocked this request.",
        ) from exc
    except ProviderRateBudgetExceeded as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Local research rate budget is exhausted. Try again shortly.",
        ) from exc
    except ProviderExecutionError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="A public-source provider failed to complete the request.",
        ) from exc

    AUDIT_STORE.record(
        "file.review.research_case",
        case_id=record.id,
        details={"mode": payload.mode.value, "kind": record.seed_kind.value},
    )
    return ReviewedCandidateCaseResponse(
        case_id=record.id,
        mode=payload.mode,
        seed_kind=record.seed_kind,
        created_at=record.created_at,
        expires_at=record.expires_at,
    )
