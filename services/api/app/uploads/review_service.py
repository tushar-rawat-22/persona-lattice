# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from uuid import UUID

from ..intelligence import LeadCandidate
from .candidates import confirm_candidate, reject_candidate
from .contracts import ReviewCandidate, ReviewStatus
from .promotion import promote_confirmed_identifier_candidate
from .review_store import UPLOAD_REVIEW_STORE, UploadReviewStore


class UploadReviewCandidateNotFoundError(LookupError):
    """Raised when a server-owned upload review candidate no longer exists."""


def _require_candidate(candidate: ReviewCandidate | None) -> ReviewCandidate:
    if candidate is None:
        raise UploadReviewCandidateNotFoundError(
            "Upload review candidate was not found or has expired."
        )
    return candidate


def confirm_stored_candidate(
    artifact_id: UUID,
    candidate_id: UUID,
    *,
    store: UploadReviewStore = UPLOAD_REVIEW_STORE,
) -> ReviewCandidate:
    """Confirm one server-owned candidate and authorize identifier research."""

    return _require_candidate(
        store.mutate(
            artifact_id,
            candidate_id,
            lambda candidate: confirm_candidate(candidate, human_confirmed=True),
        )
    )


def reject_stored_candidate(
    artifact_id: UUID,
    candidate_id: UUID,
    *,
    store: UploadReviewStore = UPLOAD_REVIEW_STORE,
) -> ReviewCandidate:
    """Reject one server-owned candidate and revoke research authorization."""

    return _require_candidate(
        store.mutate(artifact_id, candidate_id, reject_candidate)
    )


def reopen_stored_candidate(
    artifact_id: UUID,
    candidate_id: UUID,
    *,
    store: UploadReviewStore = UPLOAD_REVIEW_STORE,
) -> ReviewCandidate:
    """Return a prior review decision to pending without changing provenance."""

    def reopen(candidate: ReviewCandidate) -> ReviewCandidate:
        return candidate.model_copy(
            update={
                "review_status": ReviewStatus.PENDING,
                "external_research_authorized": False,
            }
        )

    return _require_candidate(store.mutate(artifact_id, candidate_id, reopen))


def promote_stored_candidate(
    artifact_id: UUID,
    candidate_id: UUID,
    *,
    store: UploadReviewStore = UPLOAD_REVIEW_STORE,
) -> LeadCandidate:
    """Promote only the current server-owned confirmed candidate snapshot."""

    candidate = _require_candidate(store.get(artifact_id, candidate_id))
    return promote_confirmed_identifier_candidate(candidate)
