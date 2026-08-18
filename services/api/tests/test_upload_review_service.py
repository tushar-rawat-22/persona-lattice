# SPDX-License-Identifier: Apache-2.0
from pathlib import Path
from uuid import uuid4

import pytest

from app.evidence import IdentifierKind
from app.intelligence import LeadKind, LeadReason
from app.uploads.candidates import CandidateReviewError
from app.uploads.contracts import (
    ArtifactPreview,
    CandidateOrigin,
    CandidateType,
    FileBatchPreview,
    ReviewCandidate,
    ReviewStatus,
)
from app.uploads.review_service import (
    UploadReviewCandidateNotFoundError,
    confirm_stored_candidate,
    promote_stored_candidate,
    reject_stored_candidate,
    reopen_stored_candidate,
)
from app.uploads.review_store import UploadReviewStore


def _saved_candidate(monkeypatch, tmp_path: Path) -> tuple[UploadReviewStore, ReviewCandidate]:
    monkeypatch.setenv("PERSONALATTICE_DB_PATH", str(tmp_path / "review.db"))
    monkeypatch.setenv("PERSONALATTICE_UPLOAD_REVIEW_RETENTION_HOURS", "24")
    store = UploadReviewStore()
    artifact_id = uuid4()
    value = "analyst@example.test"
    candidate = ReviewCandidate(
        candidate_id=uuid4(),
        candidate_type=CandidateType.IDENTIFIER,
        origin=CandidateOrigin.RULE,
        source_artifact_id=artifact_id,
        identifier_kind=IdentifierKind.EMAIL,
        value=value,
        source_start=8,
        source_end=8 + len(value),
    )
    text = f"Contact {value} for review."
    preview = FileBatchPreview(
        artifacts=[
            ArtifactPreview(
                artifact_id=artifact_id,
                original_name="synthetic.txt",
                size_bytes=len(text.encode()),
                sha256="0" * 64,
                detected_media_type="text/plain",
                extraction_method="utf8_text",
                extracted_text=text,
                extracted_chars=len(text),
                candidates=[candidate],
            )
        ]
    )
    assert store.save_preview(preview) == 1
    return store, candidate


def test_confirm_reject_and_reopen_only_change_review_authorization(
    monkeypatch,
    tmp_path: Path,
) -> None:
    store, original = _saved_candidate(monkeypatch, tmp_path)

    confirmed = confirm_stored_candidate(
        original.source_artifact_id,
        original.candidate_id,
        store=store,
    )
    assert confirmed.review_status is ReviewStatus.CONFIRMED
    assert confirmed.external_research_authorized is True
    assert confirmed.value == original.value
    assert confirmed.identifier_kind is original.identifier_kind
    assert confirmed.source_start == original.source_start
    assert confirmed.source_end == original.source_end

    rejected = reject_stored_candidate(
        original.source_artifact_id,
        original.candidate_id,
        store=store,
    )
    assert rejected.review_status is ReviewStatus.REJECTED
    assert rejected.external_research_authorized is False

    reopened = reopen_stored_candidate(
        original.source_artifact_id,
        original.candidate_id,
        store=store,
    )
    assert reopened.review_status is ReviewStatus.PENDING
    assert reopened.external_research_authorized is False
    assert reopened.value == original.value


def test_promotion_reads_current_server_owned_state_and_preserves_provenance(
    monkeypatch,
    tmp_path: Path,
) -> None:
    store, candidate = _saved_candidate(monkeypatch, tmp_path)

    with pytest.raises(CandidateReviewError, match="not authorized"):
        promote_stored_candidate(
            candidate.source_artifact_id,
            candidate.candidate_id,
            store=store,
        )

    confirm_stored_candidate(
        candidate.source_artifact_id,
        candidate.candidate_id,
        store=store,
    )
    lead = promote_stored_candidate(
        candidate.source_artifact_id,
        candidate.candidate_id,
        store=store,
    )

    assert lead.kind is LeadKind.EMAIL
    assert lead.value == candidate.value
    assert lead.reason is LeadReason.REVIEWED_DOCUMENT_IDENTIFIER
    assert lead.source == "reviewed_upload_candidate"
    assert f"artifact://{candidate.source_artifact_id}" in lead.source_locator
    assert f"candidate={candidate.candidate_id}" in lead.source_locator
    assert f"offset={candidate.source_start}-{candidate.source_end}" in lead.source_locator

    reject_stored_candidate(
        candidate.source_artifact_id,
        candidate.candidate_id,
        store=store,
    )
    with pytest.raises(CandidateReviewError, match="not authorized"):
        promote_stored_candidate(
            candidate.source_artifact_id,
            candidate.candidate_id,
            store=store,
        )


def test_review_service_requires_exact_server_owned_artifact_and_candidate_ids(
    monkeypatch,
    tmp_path: Path,
) -> None:
    store, candidate = _saved_candidate(monkeypatch, tmp_path)

    with pytest.raises(UploadReviewCandidateNotFoundError, match="not found or has expired"):
        confirm_stored_candidate(
            uuid4(),
            candidate.candidate_id,
            store=store,
        )
    with pytest.raises(UploadReviewCandidateNotFoundError, match="not found or has expired"):
        confirm_stored_candidate(
            candidate.source_artifact_id,
            uuid4(),
            store=store,
        )

    persisted = store.get(candidate.source_artifact_id, candidate.candidate_id)
    assert persisted is not None
    assert persisted.review_status is ReviewStatus.PENDING
    assert persisted.external_research_authorized is False


def test_atomic_mutation_rejects_value_or_provenance_changes_and_rolls_back(
    monkeypatch,
    tmp_path: Path,
) -> None:
    store, candidate = _saved_candidate(monkeypatch, tmp_path)

    with pytest.raises(RuntimeError, match="cannot alter candidate value or provenance"):
        store.mutate(
            candidate.source_artifact_id,
            candidate.candidate_id,
            lambda stored: stored.model_copy(update={"value": "tampered@example.test"}),
        )

    persisted = store.get(candidate.source_artifact_id, candidate.candidate_id)
    assert persisted is not None
    assert persisted.value == candidate.value
    assert persisted.review_status is ReviewStatus.PENDING
    assert persisted.external_research_authorized is False


def test_atomic_mutation_requires_review_candidate_result(
    monkeypatch,
    tmp_path: Path,
) -> None:
    store, candidate = _saved_candidate(monkeypatch, tmp_path)

    with pytest.raises(TypeError, match="must return ReviewCandidate"):
        store.mutate(
            candidate.source_artifact_id,
            candidate.candidate_id,
            lambda _stored: None,  # type: ignore[return-value]
        )

    persisted = store.get(candidate.source_artifact_id, candidate.candidate_id)
    assert persisted is not None
    assert persisted.review_status is ReviewStatus.PENDING
