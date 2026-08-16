# SPDX-License-Identifier: Apache-2.0
from uuid import uuid4

from app.evidence import (
    EvidenceStore,
    ObservationSourceKind,
    create_database_engine,
    create_schema,
    make_session_factory,
)
from app.uploads import ArtifactPreview, record_upload_observation


def test_extraction_observation_keeps_artifact_provenance() -> None:
    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    create_schema(engine)
    factory = make_session_factory(engine)

    artifact_id = uuid4()
    artifact = ArtifactPreview(
        artifact_id=artifact_id,
        original_name="synthetic.txt",
        size_bytes=31,
        sha256="a" * 64,
        detected_media_type="text/plain",
        extraction_method="utf8_text",
        extracted_text="Synthetic document content.",
        extracted_chars=27,
    )

    with factory() as session:
        store = EvidenceStore(session)
        subject = store.add_subject("Synthetic Person")
        observation = record_upload_observation(
            store,
            subject_id=subject.id,
            artifact=artifact,
        )

        assert observation.source_kind == ObservationSourceKind.UPLOAD
        assert observation.source_locator == f"artifact://{artifact_id}"
        assert observation.payload["sha256"] == "a" * 64
        assert observation.payload["trust_boundary"] == "untrusted_uploaded_content"
        assert observation.payload["extracted_text"] == "Synthetic document content."
