# SPDX-License-Identifier: Apache-2.0
from pathlib import Path
from uuid import uuid4

import pytest

from app.evidence import IdentifierKind
from app.uploads.contracts import (
    ArtifactPreview,
    CandidateOrigin,
    CandidateType,
    FileBatchPreview,
    ReviewCandidate,
    ReviewStatus,
)
from app.uploads.review_store import UploadReviewStore


def test_generic_update_cannot_bypass_review_field_immutability(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("PERSONALATTICE_DB_PATH", str(tmp_path / "review.db"))
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

    tampered = candidate.model_copy(update={"value": "tampered@example.test"})
    with pytest.raises(RuntimeError, match="cannot alter candidate value or provenance"):
        store.update(tampered)

    confirmed = candidate.model_copy(
        update={
            "review_status": ReviewStatus.CONFIRMED,
            "external_research_authorized": True,
        }
    )
    assert store.update(confirmed) is True

    persisted = store.get(artifact_id, candidate.candidate_id)
    assert persisted is not None
    assert persisted.value == value
    assert persisted.review_status is ReviewStatus.CONFIRMED
    assert persisted.external_research_authorized is True
