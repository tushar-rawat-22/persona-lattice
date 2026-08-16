# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import sqlite3
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class AuditEvent:
    id: UUID
    created_at: datetime
    event_type: str
    case_id: UUID | None
    details: dict[str, object]


def _database_path() -> Path:
    raw = os.environ.get("PERSONALATTICE_DB_PATH", "./personalattice.db").strip()
    if not raw:
        raise RuntimeError("PERSONALATTICE_DB_PATH is empty.")
    path = Path(raw).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(_database_path(), timeout=10.0)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA busy_timeout = 10000")
    connection.execute("PRAGMA journal_mode = WAL")
    return connection


def _initialize(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_events (
            id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            event_type TEXT NOT NULL,
            case_id TEXT,
            details_json TEXT NOT NULL
        )
        """
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_audit_events_created_at ON audit_events(created_at DESC)"
    )
    connection.commit()


def _decode(row: sqlite3.Row) -> AuditEvent:
    return AuditEvent(
        id=UUID(row["id"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        event_type=row["event_type"],
        case_id=UUID(row["case_id"]) if row["case_id"] else None,
        details=json.loads(row["details_json"]),
    )


class AuditStore:
    """Minimal operational audit trail that deliberately excludes research seed values.

    Audit events can identify a retained case by UUID and record bounded operational
    metadata, but they must not copy emails, phone numbers, usernames, URLs, session
    secrets, CSRF tokens, passwords or provider response payloads.
    """

    def record(
        self,
        event_type: str,
        *,
        case_id: UUID | None = None,
        details: dict[str, object] | None = None,
        now: datetime | None = None,
    ) -> AuditEvent:
        normalized_event_type = event_type.strip()
        if not normalized_event_type or len(normalized_event_type) > 80:
            raise ValueError("audit event_type must contain 1 to 80 characters")
        payload = dict(details or {})
        serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        if len(serialized.encode("utf-8")) > 4096:
            raise ValueError("audit details exceed the configured limit")

        event = AuditEvent(
            id=uuid4(),
            created_at=now or datetime.now(UTC),
            event_type=normalized_event_type,
            case_id=case_id,
            details=payload,
        )
        with _connect() as connection:
            _initialize(connection)
            connection.execute(
                """
                INSERT INTO audit_events (id, created_at, event_type, case_id, details_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    str(event.id),
                    event.created_at.isoformat(),
                    event.event_type,
                    str(event.case_id) if event.case_id else None,
                    serialized,
                ),
            )
            connection.commit()
        return event

    def list_recent(self, *, limit: int = 100) -> list[AuditEvent]:
        if not 1 <= limit <= 500:
            raise ValueError("audit list limit must be between 1 and 500")
        with _connect() as connection:
            _initialize(connection)
            rows = connection.execute(
                "SELECT * FROM audit_events ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [_decode(row) for row in rows]


AUDIT_STORE = AuditStore()
