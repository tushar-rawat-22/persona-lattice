# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import json
import re
import sqlite3
from uuid import UUID, uuid4

from .sqlite_storage import private_runtime_database_path


@dataclass(frozen=True, slots=True)
class AuditEvent:
    id: UUID
    created_at: datetime
    event_type: str
    case_id: UUID | None
    details: dict[str, object]


# Audit metadata is intentionally schema-limited. The audit table is an
# operational trail, not a second evidence store. Adding a new event or detail
# key should therefore be an explicit privacy decision rather than something a
# caller can persist opportunistically.
_ALLOWED_DETAIL_KEYS_BY_EVENT: dict[str, frozenset[str]] = {
    "auth.login_success": frozenset(),
    "auth.logout": frozenset(),
    "research.quick": frozenset({"kind"}),
    "research.converged": frozenset({"kind", "node_count"}),
    "case.create": frozenset({"mode", "node_count"}),
    "case.list": frozenset({"result_count", "has_more"}),
    "case.purge_expired": frozenset({"count"}),
    "case.delete_all": frozenset({"count"}),
    "case.read": frozenset(),
    "case.delete": frozenset({"deleted"}),
    "file.preview": frozenset({"file_count"}),
    "file.review.confirm": frozenset({"candidate_type", "identifier_kind"}),
    "file.review.reject": frozenset({"candidate_type", "identifier_kind"}),
    "file.review.reopen": frozenset({"candidate_type", "identifier_kind"}),
    "file.review.promote": frozenset({"kind"}),
    "file.review.research_case": frozenset({"mode", "kind"}),
}
_EVENT_TYPE_RE = re.compile(r"^[a-z][a-z0-9_.-]{0,79}$")
_SAFE_KIND_VALUES = frozenset({"username", "phone", "email", "url", "domain"})
_SAFE_MODE_VALUES = frozenset({"quick", "converged"})
_SAFE_CANDIDATE_TYPE_VALUES = frozenset({"identifier", "claim"})
_SAFE_IDENTIFIER_KIND_VALUES = frozenset(
    {"name", "phone", "email", "username", "url", "domain", "organization"}
)
_COUNT_DETAIL_KEYS = frozenset({"node_count", "result_count", "count", "file_count"})
_BOOL_DETAIL_KEYS = frozenset({"has_more", "deleted"})


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(private_runtime_database_path(), timeout=10.0)
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


def _validate_detail_value(key: str, value: object) -> None:
    if key in _COUNT_DETAIL_KEYS:
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 1_000_000_000:
            raise ValueError(f"audit detail {key!r} must be a bounded non-negative integer")
        return
    if key in _BOOL_DETAIL_KEYS:
        if not isinstance(value, bool):
            raise ValueError(f"audit detail {key!r} must be boolean")
        return
    if key == "kind":
        if value not in _SAFE_KIND_VALUES:
            raise ValueError("audit detail 'kind' is outside the approved vocabulary")
        return
    if key == "mode":
        if value not in _SAFE_MODE_VALUES:
            raise ValueError("audit detail 'mode' is outside the approved vocabulary")
        return
    if key == "candidate_type":
        if value not in _SAFE_CANDIDATE_TYPE_VALUES:
            raise ValueError("audit detail 'candidate_type' is outside the approved vocabulary")
        return
    if key == "identifier_kind":
        if value is not None and value not in _SAFE_IDENTIFIER_KIND_VALUES:
            raise ValueError("audit detail 'identifier_kind' is outside the approved vocabulary")
        return
    raise ValueError(f"audit detail key {key!r} has no approved value contract")


def _validate_details(event_type: str, payload: dict[str, object]) -> None:
    allowed = _ALLOWED_DETAIL_KEYS_BY_EVENT.get(event_type)
    if allowed is None:
        raise ValueError("audit event type is outside the approved vocabulary")
    unexpected = set(payload).difference(allowed)
    if unexpected:
        raise ValueError("audit details contain an unapproved key")
    for key, value in payload.items():
        _validate_detail_value(key, value)


class AuditStore:
    """Minimal operational audit trail that deliberately excludes research seed values.

    Audit events can identify a retained case by UUID and record only explicitly
    approved operational metadata. Emails, phone numbers, usernames, URLs,
    passwords, hashes, session/CSRF tokens, provider secrets, raw upload content
    and provider payloads have no permitted audit detail field.
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
        if _EVENT_TYPE_RE.fullmatch(normalized_event_type) is None:
            raise ValueError("audit event_type has an invalid format")
        payload = dict(details or {})
        _validate_details(normalized_event_type, payload)
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
