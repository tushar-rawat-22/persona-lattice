# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
import json
import os
from pathlib import Path
import sqlite3
from uuid import UUID, uuid4

from .intelligence.source_reporting import build_source_run_report
from .reporting import build_structured_report
from .research import QuickResearchReport, ResearchKind


_DEFAULT_RETENTION_DAYS = 30
_MAX_RETENTION_DAYS = 365


@dataclass(frozen=True, slots=True)
class StoredCase:
    id: UUID
    created_at: datetime
    expires_at: datetime
    seed_kind: ResearchKind
    seed_value: str
    report: dict[str, object]


def _database_path() -> Path:
    raw = os.environ.get("PERSONALATTICE_DB_PATH", "./personalattice.db").strip()
    if not raw:
        raise RuntimeError("PERSONALATTICE_DB_PATH is empty.")
    path = Path(raw).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _retention_days() -> int:
    raw = os.environ.get("PERSONALATTICE_CASE_RETENTION_DAYS", str(_DEFAULT_RETENTION_DAYS))
    try:
        days = int(raw)
    except ValueError as exc:
        raise RuntimeError("Case retention configuration is invalid.") from exc
    if not 1 <= days <= _MAX_RETENTION_DAYS:
        raise RuntimeError("Case retention must be between 1 and 365 days.")
    return days


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(_database_path(), timeout=10.0)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 10000")
    connection.execute("PRAGMA journal_mode = WAL")
    return connection


def _initialize(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS research_cases (
            id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            seed_kind TEXT NOT NULL,
            seed_value TEXT NOT NULL,
            report_json TEXT NOT NULL
        )
        """
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_research_cases_created_at ON research_cases(created_at DESC)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_research_cases_expires_at ON research_cases(expires_at)"
    )
    connection.commit()


def _report_payload(
    report: QuickResearchReport,
    *,
    seed_provenance: dict[str, object] | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "kind": report.kind.value,
        "normalized_value": report.normalized_value,
        "observations": [asdict(item) for item in report.observations],
        "warnings": list(report.warnings),
        "source_runs": build_source_run_report(report.source_runs),
        "structured_report": build_structured_report(report),
    }
    if seed_provenance is not None:
        payload["seed_provenance"] = dict(seed_provenance)
    return payload


def _decode_row(row: sqlite3.Row) -> StoredCase:
    return StoredCase(
        id=UUID(row["id"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        expires_at=datetime.fromisoformat(row["expires_at"]),
        seed_kind=ResearchKind(row["seed_kind"]),
        seed_value=row["seed_value"],
        report=json.loads(row["report_json"]),
    )


class CaseStore:
    def purge_expired(self, *, now: datetime | None = None) -> int:
        evaluated_at = now or datetime.now(UTC)
        with _connect() as connection:
            _initialize(connection)
            cursor = connection.execute(
                "DELETE FROM research_cases WHERE expires_at <= ?",
                (evaluated_at.isoformat(),),
            )
            connection.commit()
            return cursor.rowcount

    def create_payload(
        self,
        *,
        seed_kind: ResearchKind,
        seed_value: str,
        report_payload: dict[str, object],
        now: datetime | None = None,
    ) -> StoredCase:
        created_at = now or datetime.now(UTC)
        expires_at = created_at + timedelta(days=_retention_days())
        record = StoredCase(
            id=uuid4(),
            created_at=created_at,
            expires_at=expires_at,
            seed_kind=seed_kind,
            seed_value=seed_value,
            report=report_payload,
        )
        serialized = json.dumps(record.report, ensure_ascii=False, separators=(",", ":"))
        with _connect() as connection:
            _initialize(connection)
            connection.execute(
                """
                INSERT INTO research_cases
                    (id, created_at, expires_at, seed_kind, seed_value, report_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(record.id),
                    record.created_at.isoformat(),
                    record.expires_at.isoformat(),
                    record.seed_kind.value,
                    record.seed_value,
                    serialized,
                ),
            )
            connection.commit()
        return record

    def create(
        self,
        *,
        seed_kind: ResearchKind,
        seed_value: str,
        report: QuickResearchReport,
        seed_provenance: dict[str, object] | None = None,
        now: datetime | None = None,
    ) -> StoredCase:
        return self.create_payload(
            seed_kind=seed_kind,
            seed_value=seed_value,
            report_payload=_report_payload(report, seed_provenance=seed_provenance),
            now=now,
        )

    def get(self, case_id: UUID, *, now: datetime | None = None) -> StoredCase | None:
        evaluated_at = now or datetime.now(UTC)
        with _connect() as connection:
            _initialize(connection)
            row = connection.execute(
                "SELECT * FROM research_cases WHERE id = ?",
                (str(case_id),),
            ).fetchone()
            if row is None:
                return None
            record = _decode_row(row)
            if record.expires_at <= evaluated_at:
                connection.execute("DELETE FROM research_cases WHERE id = ?", (str(case_id),))
                connection.commit()
                return None
            return record

    def list_recent(self, *, limit: int = 20, now: datetime | None = None) -> list[StoredCase]:
        if not 1 <= limit <= 100:
            raise ValueError("Case list limit must be between 1 and 100.")
        self.purge_expired(now=now)
        with _connect() as connection:
            _initialize(connection)
            rows = connection.execute(
                "SELECT * FROM research_cases ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [_decode_row(row) for row in rows]

    def delete(self, case_id: UUID) -> bool:
        with _connect() as connection:
            _initialize(connection)
            cursor = connection.execute(
                "DELETE FROM research_cases WHERE id = ?",
                (str(case_id),),
            )
            connection.commit()
            return cursor.rowcount > 0

    def delete_all(self) -> int:
        with _connect() as connection:
            _initialize(connection)
            cursor = connection.execute("DELETE FROM research_cases")
            connection.commit()
            return cursor.rowcount


CASE_STORE = CaseStore()
