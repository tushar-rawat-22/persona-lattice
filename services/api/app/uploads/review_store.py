# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
import os
import sqlite3
from uuid import UUID

from ..sqlite_storage import private_runtime_database_path
from .contracts import FileBatchPreview, ReviewCandidate


_DEFAULT_RETENTION_HOURS = 24
_MAX_RETENTION_HOURS = 168
_MUTABLE_REVIEW_FIELDS = frozenset({"review_status", "external_research_authorized"})


def _retention_hours() -> int:
    raw = os.environ.get(
        "PERSONALATTICE_UPLOAD_REVIEW_RETENTION_HOURS",
        str(_DEFAULT_RETENTION_HOURS),
    )
    try:
        hours = int(raw)
    except ValueError as exc:
        raise RuntimeError("Upload review retention configuration is invalid.") from exc
    if not 1 <= hours <= _MAX_RETENTION_HOURS:
        raise RuntimeError("Upload review retention must be between 1 and 168 hours.")
    return hours


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(private_runtime_database_path(), timeout=10.0)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 10000")
    connection.execute("PRAGMA journal_mode = WAL")
    return connection


def _initialize(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS upload_review_candidates (
            candidate_id TEXT PRIMARY KEY,
            artifact_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            candidate_json TEXT NOT NULL
        )
        """
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_upload_review_artifact "
        "ON upload_review_candidates(artifact_id, created_at)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_upload_review_expires "
        "ON upload_review_candidates(expires_at)"
    )
    connection.commit()


def _decode_candidate(row: sqlite3.Row) -> ReviewCandidate:
    candidate = ReviewCandidate.model_validate_json(row["candidate_json"])
    if str(candidate.candidate_id) != row["candidate_id"]:
        raise RuntimeError("Stored upload-review candidate ID does not match its row key.")
    if str(candidate.source_artifact_id) != row["artifact_id"]:
        raise RuntimeError("Stored upload-review artifact ID does not match its row key.")
    return candidate


def _immutable_payload(candidate: ReviewCandidate) -> dict[str, object]:
    return candidate.model_dump(exclude=_MUTABLE_REVIEW_FIELDS)


class UploadReviewStore:
    """Short-lived server-owned candidate state for explicit upload review.

    The store retains only candidate metadata/value needed for review and
    promotion. Raw extracted document text, filenames and file bytes are never
    copied into this table.
    """

    def purge_expired(self, *, now: datetime | None = None) -> int:
        evaluated_at = now or datetime.now(UTC)
        with _connect() as connection:
            _initialize(connection)
            cursor = connection.execute(
                "DELETE FROM upload_review_candidates WHERE expires_at <= ?",
                (evaluated_at.isoformat(),),
            )
            connection.commit()
            return cursor.rowcount

    def save_preview(
        self,
        preview: FileBatchPreview,
        *,
        now: datetime | None = None,
    ) -> int:
        created_at = now or datetime.now(UTC)
        expires_at = created_at + timedelta(hours=_retention_hours())
        candidates = [
            candidate
            for artifact in preview.artifacts
            for candidate in artifact.candidates
        ]
        self.purge_expired(now=created_at)
        if not candidates:
            return 0

        rows = [
            (
                str(candidate.candidate_id),
                str(candidate.source_artifact_id),
                created_at.isoformat(),
                created_at.isoformat(),
                expires_at.isoformat(),
                candidate.model_dump_json(),
            )
            for candidate in candidates
        ]
        with _connect() as connection:
            _initialize(connection)
            connection.executemany(
                """
                INSERT INTO upload_review_candidates
                    (candidate_id, artifact_id, created_at, updated_at, expires_at, candidate_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
            connection.commit()
        return len(rows)

    def get(
        self,
        artifact_id: UUID,
        candidate_id: UUID,
        *,
        now: datetime | None = None,
    ) -> ReviewCandidate | None:
        evaluated_at = now or datetime.now(UTC)
        with _connect() as connection:
            _initialize(connection)
            row = connection.execute(
                """
                SELECT * FROM upload_review_candidates
                WHERE artifact_id = ? AND candidate_id = ?
                """,
                (str(artifact_id), str(candidate_id)),
            ).fetchone()
            if row is None:
                return None
            if datetime.fromisoformat(row["expires_at"]) <= evaluated_at:
                connection.execute(
                    "DELETE FROM upload_review_candidates WHERE candidate_id = ?",
                    (str(candidate_id),),
                )
                connection.commit()
                return None
            return _decode_candidate(row)

    def list_for_artifact(
        self,
        artifact_id: UUID,
        *,
        now: datetime | None = None,
    ) -> list[ReviewCandidate]:
        evaluated_at = now or datetime.now(UTC)
        self.purge_expired(now=evaluated_at)
        with _connect() as connection:
            _initialize(connection)
            rows = connection.execute(
                """
                SELECT * FROM upload_review_candidates
                WHERE artifact_id = ?
                ORDER BY created_at, candidate_id
                """,
                (str(artifact_id),),
            ).fetchall()
        return [_decode_candidate(row) for row in rows]

    def mutate(
        self,
        artifact_id: UUID,
        candidate_id: UUID,
        transform: Callable[[ReviewCandidate], ReviewCandidate],
        *,
        now: datetime | None = None,
    ) -> ReviewCandidate | None:
        """Atomically mutate review authorization fields on server-owned state.

        The transaction serializes concurrent operator mutations for the same
        SQLite database. Candidate value, kind and provenance are immutable here;
        only review status and external-research authorization may change.
        """

        updated_at = now or datetime.now(UTC)
        with _connect() as connection:
            _initialize(connection)
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                """
                SELECT * FROM upload_review_candidates
                WHERE artifact_id = ? AND candidate_id = ?
                """,
                (str(artifact_id), str(candidate_id)),
            ).fetchone()
            if row is None:
                connection.commit()
                return None
            if datetime.fromisoformat(row["expires_at"]) <= updated_at:
                connection.execute(
                    "DELETE FROM upload_review_candidates WHERE candidate_id = ?",
                    (str(candidate_id),),
                )
                connection.commit()
                return None

            current = _decode_candidate(row)
            candidate = transform(current)
            if not isinstance(candidate, ReviewCandidate):
                raise TypeError("Upload review transform must return ReviewCandidate.")
            if _immutable_payload(candidate) != _immutable_payload(current):
                raise RuntimeError("Upload review mutation cannot alter candidate value or provenance.")

            cursor = connection.execute(
                """
                UPDATE upload_review_candidates
                SET updated_at = ?, candidate_json = ?
                WHERE candidate_id = ? AND artifact_id = ? AND expires_at > ?
                """,
                (
                    updated_at.isoformat(),
                    candidate.model_dump_json(),
                    str(candidate_id),
                    str(artifact_id),
                    updated_at.isoformat(),
                ),
            )
            if cursor.rowcount != 1:
                raise RuntimeError("Upload review candidate changed during mutation.")
            connection.commit()
            return candidate

    def update(
        self,
        candidate: ReviewCandidate,
        *,
        now: datetime | None = None,
    ) -> bool:
        """Persist review-only changes through the same immutable-field guard."""

        return (
            self.mutate(
                candidate.source_artifact_id,
                candidate.candidate_id,
                lambda _current: candidate,
                now=now,
            )
            is not None
        )

    def delete_all(self) -> int:
        with _connect() as connection:
            _initialize(connection)
            cursor = connection.execute("DELETE FROM upload_review_candidates")
            connection.commit()
            return cursor.rowcount


UPLOAD_REVIEW_STORE = UploadReviewStore()
