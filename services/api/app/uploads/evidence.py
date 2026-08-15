# SPDX-License-Identifier: Apache-2.0
from uuid import UUID

from ..evidence import EvidenceStore, Observation, ObservationSourceKind
from .contracts import ArtifactPreview


def record_upload_observation(
    store: EvidenceStore,
    *,
    subject_id: UUID,
    artifact: ArtifactPreview,
) -> Observation:
    return store.add_observation(
        subject_id=subject_id,
        source_kind=ObservationSourceKind.UPLOAD,
        source_name="Uploaded document",
        source_locator=f"artifact://{artifact.artifact_id}",
        payload={
            "artifact_id": str(artifact.artifact_id),
            "original_name": artifact.original_name,
            "sha256": artifact.sha256,
            "detected_media_type": artifact.detected_media_type,
            "extraction_method": artifact.extraction_method,
            "extracted_text": artifact.extracted_text,
            "trust_boundary": artifact.trust_boundary,
        },
    )
