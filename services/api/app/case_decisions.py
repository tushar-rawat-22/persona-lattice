# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
import sqlite3
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from .admin_auth import require_admin, require_admin_write
from .audit import AUDIT_STORE
from .authz import AuthenticatedPrincipal
from .cases import CASE_STORE
from .sqlite_storage import private_runtime_database_path


router = APIRouter(prefix="/v1/cases", tags=["case-decisions"])

_MAX_DECISION_ENTRIES = 100


class CaseDecisionDisposition(StrEnum):
    CONTINUE_RESEARCH = "continue_research"
    AWAIT_MORE_EVIDENCE = "await_more_evidence"
    READY_FOR_HANDOFF = "ready_for_handoff"
    CLOSE_CASE = "close_case"


class CaseDecisionRequest(BaseModel):
    disposition: CaseDecisionDisposition
    rationale: str = Field(min_length=1, max_length=1200)


class CaseDecisionResponse(BaseModel):
    id: UUID
    case_id: UUID
    created_at: datetime
    disposition: CaseDecisionDisposition
    rationale: str


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
        CREATE TABLE IF NOT EXISTS case_decisions (
            id TEXT PRIMARY KEY,
            case_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            disposition TEXT NOT NULL,
            rationale TEXT NOT NULL,
            FOREIGN KEY (case_id) REFERENCES research_cases(id) ON DELETE CASCADE
        )
        """
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_case_decisions_case_created "
        "ON case_decisions(case_id, created_at DESC, id DESC)"
    )
    connection.commit()


def _case_not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found.")


def _response(row: sqlite3.Row) -> CaseDecisionResponse:
    return CaseDecisionResponse(
        id=UUID(row["id"]),
        case_id=UUID(row["case_id"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        disposition=CaseDecisionDisposition(row["disposition"]),
        rationale=row["rationale"],
    )


@router.get("/{case_id}/decisions", response_model=list[CaseDecisionResponse])
def list_case_decisions(
    case_id: UUID,
    _principal: AuthenticatedPrincipal = Depends(require_admin),
) -> list[CaseDecisionResponse]:
    if CASE_STORE.get(case_id) is None:
        raise _case_not_found()

    with _connect() as connection:
        _initialize(connection)
        rows = connection.execute(
            """
            SELECT id, case_id, created_at, disposition, rationale
            FROM case_decisions
            WHERE case_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (str(case_id), _MAX_DECISION_ENTRIES),
        ).fetchall()
    return [_response(row) for row in rows]


@router.post(
    "/{case_id}/decisions",
    response_model=CaseDecisionResponse,
    status_code=status.HTTP_201_CREATED,
)
def append_case_decision(
    case_id: UUID,
    payload: CaseDecisionRequest,
    _principal: AuthenticatedPrincipal = Depends(require_admin_write),
) -> CaseDecisionResponse:
    if CASE_STORE.get(case_id) is None:
        raise _case_not_found()

    rationale = payload.rationale.strip()
    if not rationale:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Decision rationale must contain non-whitespace text.",
        )

    decision_id = uuid4()
    created_at = datetime.now(UTC)
    with _connect() as connection:
        _initialize(connection)
        connection.execute(
            """
            INSERT INTO case_decisions (id, case_id, created_at, disposition, rationale)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                str(decision_id),
                str(case_id),
                created_at.isoformat(),
                payload.disposition.value,
                rationale,
            ),
        )
        connection.commit()

    AUDIT_STORE.record(
        "case.decision.append",
        case_id=case_id,
        details={"disposition": payload.disposition.value},
    )
    return CaseDecisionResponse(
        id=decision_id,
        case_id=case_id,
        created_at=created_at,
        disposition=payload.disposition,
        rationale=rationale,
    )
