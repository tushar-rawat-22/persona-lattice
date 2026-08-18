# SPDX-License-Identifier: Apache-2.0
from datetime import UTC, datetime, timedelta
from pathlib import Path
import sqlite3
from uuid import uuid4

from fastapi.testclient import TestClient

from app.admin_auth import LOGIN_THROTTLE, SESSION_STORE, hash_admin_password
from app.main import app
from app.uploads import (
    UPLOAD_REVIEW_STORE,
    ArtifactPreview,
    CandidateOrigin,
    CandidateType,
    FileBatchPreview,
    ReviewCandidate,
)
from app.evidence import IdentifierKind


client = TestClient(app)
PASSWORD = "synthetic-admin-password-123!"


def _configure_and_login(monkeypatch, database_path: Path) -> str:
    client.cookies.clear()
    SESSION_STORE.clear()
    LOGIN_THROTTLE.clear()
    monkeypatch.setenv("PERSONALATTICE_ADMIN_USERNAME", "admin")
    monkeypatch.setenv("PERSONALATTICE_ADMIN_PASSWORD_HASH", hash_admin_password(PASSWORD))
    monkeypatch.setenv("PERSONALATTICE_COOKIE_SECURE", "false")
    monkeypatch.setenv("PERSONALATTICE_SESSION_COOKIE", "personalattice_review_test_session")
    monkeypatch.setenv("PERSONALATTICE_DB_PATH", str(database_path))
    response = client.post(
        "/v1/auth/login",
        json={"username": "admin", "password": PASSWORD},
    )
    assert response.status_code == 200, response.text
    return response.json()["csrf_token"]


def test_file_preview_persists_server_owned_candidate_without_raw_document_text(
    monkeypatch,
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "personalattice.db"
    csrf = _configure_and_login(monkeypatch, database_path)
    monkeypatch.setenv("PERSONALATTICE_UPLOAD_DIR", str(tmp_path / "uploads"))

    raw_text = "private surrounding prose Contact analyst@example.test end marker"
    response = client.post(
        "/v1/files/preview",
        headers={"X-PersonaLattice-CSRF": csrf},
        data={"purpose": "self_audit", "consent_acknowledged": "true"},
        files=[("files", ("synthetic.txt", raw_text.encode(), "text/plain"))],
    )

    assert response.status_code == 200, response.text
    artifact = response.json()["artifacts"][0]
    candidate = next(
        item for item in artifact["candidates"] if item["identifier_kind"] == "email"
    )

    stored = UPLOAD_REVIEW_STORE.get(
        uuid4() if False else __import__("uuid").UUID(artifact["artifact_id"]),
        __import__("uuid").UUID(candidate["candidate_id"]),
    )
    assert stored is not None
    assert stored.value == "analyst@example.test"
    assert stored.review_status.value == "pending_human_review"
    assert stored.external_research_authorized is False
    assert stored.source_start == candidate["source_start"]
    assert stored.source_end == candidate["source_end"]

    serialized_database = database_path.read_bytes()
    assert b"private surrounding prose" not in serialized_database
    assert b"end marker" not in serialized_database
    assert b"synthetic.txt" not in serialized_database


def test_review_store_requires_matching_artifact_and_expires_candidate(
    monkeypatch,
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "personalattice.db"
    monkeypatch.setenv("PERSONALATTICE_DB_PATH", str(database_path))
    monkeypatch.setenv("PERSONALATTICE_UPLOAD_REVIEW_RETENTION_HOURS", "1")
    artifact_id = uuid4()
    candidate = ReviewCandidate(
        candidate_id=uuid4(),
        candidate_type=CandidateType.IDENTIFIER,
        origin=CandidateOrigin.RULE,
        source_artifact_id=artifact_id,
        identifier_kind=IdentifierKind.USERNAME,
        value="CaseHandle",
        source_start=4,
        source_end=15,
    )
    preview = FileBatchPreview(
        artifacts=[
            ArtifactPreview(
                artifact_id=artifact_id,
                original_name="synthetic.txt",
                size_bytes=15,
                sha256="0" * 64,
                detected_media_type="text/plain",
                extraction_method="text_decode",
                extracted_text="xxx CaseHandle",
                extracted_chars=14,
                candidates=[candidate],
            )
        ]
    )
    created_at = datetime(2026, 8, 18, 3, 0, tzinfo=UTC)

    assert UPLOAD_REVIEW_STORE.save_preview(preview, now=created_at) == 1
    assert UPLOAD_REVIEW_STORE.get(artifact_id, candidate.candidate_id, now=created_at) is not None
    assert UPLOAD_REVIEW_STORE.get(uuid4(), candidate.candidate_id, now=created_at) is None
    assert (
        UPLOAD_REVIEW_STORE.get(
            artifact_id,
            candidate.candidate_id,
            now=created_at + timedelta(hours=1),
        )
        is None
    )


def test_store_decode_fails_closed_if_row_artifact_key_is_tampered(
    monkeypatch,
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "personalattice.db"
    monkeypatch.setenv("PERSONALATTICE_DB_PATH", str(database_path))
    artifact_id = uuid4()
    candidate = ReviewCandidate(
        candidate_id=uuid4(),
        candidate_type=CandidateType.IDENTIFIER,
        origin=CandidateOrigin.RULE,
        source_artifact_id=artifact_id,
        identifier_kind=IdentifierKind.EMAIL,
        value="person@example.test",
        source_start=0,
        source_end=19,
    )
    preview = FileBatchPreview(
        artifacts=[
            ArtifactPreview(
                artifact_id=artifact_id,
                original_name="synthetic.txt",
                size_bytes=19,
                sha256="1" * 64,
                detected_media_type="text/plain",
                extraction_method="text_decode",
                extracted_text="person@example.test",
                extracted_chars=19,
                candidates=[candidate],
            )
        ]
    )
    UPLOAD_REVIEW_STORE.save_preview(preview)

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            "UPDATE upload_review_candidates SET artifact_id = ? WHERE candidate_id = ?",
            (str(uuid4()), str(candidate.candidate_id)),
        )
        connection.commit()

    assert UPLOAD_REVIEW_STORE.get(artifact_id, candidate.candidate_id) is None
