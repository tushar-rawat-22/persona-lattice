# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from importlib import import_module
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.evidence import create_database_engine
from app.evidence.migrations import SQLiteSchemaMigrationError, migrate_sqlite_schema
from app.evidence.models import Base

_TABLES = (
    "subjects",
    "identifiers",
    "observations",
    "claims",
    "evidence_links",
    "correlation_runs",
    "correlation_factor_records",
)


def _current_engine(path: Path):
    import_module("app.correlation.models")
    engine = create_database_engine(f"sqlite+pysqlite:///{path}")
    Base.metadata.create_all(engine)
    return engine


def _downgrade_identifiers_to_pre_domain(engine) -> None:
    raw = engine.raw_connection()
    cursor = raw.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=OFF")
        cursor.execute("PRAGMA legacy_alter_table=ON")
        cursor.execute("BEGIN IMMEDIATE")

        current_sql = cursor.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='identifiers'"
        ).fetchone()[0]
        current_fragment = "'url', 'domain', 'organization'"
        assert current_fragment in current_sql

        legacy_sql = current_sql.replace(current_fragment, "'url', 'organization'")
        legacy_sql = legacy_sql.replace(
            "CREATE TABLE identifiers",
            "CREATE TABLE identifiers__legacy_fixture",
            1,
        )
        cursor.execute(legacy_sql)

        columns = (
            "id, subject_id, kind, raw_value, normalized_value, comparison_key, created_at"
        )
        cursor.execute(
            f"INSERT INTO identifiers__legacy_fixture ({columns}) "
            f"SELECT {columns} FROM identifiers"
        )
        cursor.execute("DROP TABLE identifiers")
        cursor.execute("ALTER TABLE identifiers__legacy_fixture RENAME TO identifiers")
        cursor.execute("CREATE INDEX ix_identifiers_subject_id ON identifiers(subject_id)")
        raw.commit()
    except Exception:
        raw.rollback()
        raise
    finally:
        cursor.execute("PRAGMA legacy_alter_table=OFF")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
        raw.close()


def _seed_evidence_graph(engine) -> dict[str, str]:
    ids = {
        name: uuid4().hex
        for name in ("subject", "identifier", "observation", "claim", "link", "run", "factor")
    }
    now = "2026-08-20 00:00:00.000000"
    raw = engine.raw_connection()
    cursor = raw.cursor()
    try:
        cursor.execute(
            "INSERT INTO subjects(id, display_name, created_at) VALUES (?, ?, ?)",
            (ids["subject"], "Migration fixture", now),
        )
        cursor.execute(
            "INSERT INTO identifiers(id, subject_id, kind, raw_value, normalized_value, "
            "comparison_key, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                ids["identifier"],
                ids["subject"],
                "email",
                "A@Example.com",
                "A@example.com",
                "A@example.com",
                now,
            ),
        )
        cursor.execute(
            "INSERT INTO observations(id, subject_id, identifier_id, source_kind, source_name, "
            "source_locator, payload, retrieved_at, observed_at, expires_at, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                ids["observation"],
                ids["subject"],
                ids["identifier"],
                "public_web",
                "fixture",
                "https://example.test/evidence",
                '{"fixture": true}',
                now,
                None,
                None,
                now,
            ),
        )
        cursor.execute(
            "INSERT INTO claims(id, subject_id, statement, confidence, origin, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                ids["claim"],
                ids["subject"],
                "Synthetic migration claim",
                0.5,
                "human",
                now,
            ),
        )
        cursor.execute(
            "INSERT INTO evidence_links(id, claim_id, observation_id, relation, rationale, "
            "created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (
                ids["link"],
                ids["claim"],
                ids["observation"],
                "supports",
                "fixture relation",
                now,
            ),
        )
        cursor.execute(
            "INSERT INTO correlation_runs(id, subject_id, candidate_observation_id, "
            "policy_version, evaluated_at, input_digest, output_digest, normalized_output, "
            "created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                ids["run"],
                ids["subject"],
                ids["observation"],
                "fixture-v1",
                now,
                "a" * 64,
                "b" * 64,
                "{}",
                now,
            ),
        )
        cursor.execute(
            "INSERT INTO correlation_factor_records(id, run_id, ordinal, kind, "
            "independence_group, base_weight, applied_weight, status, veto, observation_ids, "
            "identifier_ids, rationale) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                ids["factor"],
                ids["run"],
                0,
                "exact_identifier",
                "fixture",
                10,
                10,
                "present",
                0,
                "[]",
                "[]",
                "fixture rationale",
            ),
        )
        raw.commit()
    finally:
        cursor.close()
        raw.close()
    return ids


def _snapshot(engine) -> dict[str, list[tuple[object, ...]]]:
    with engine.connect() as connection:
        return {
            table: [tuple(row) for row in connection.exec_driver_sql(
                f"SELECT * FROM {table} ORDER BY 1"
            ).all()]
            for table in _TABLES
        }


def test_pre_domain_database_migrates_without_changing_evidence(tmp_path: Path) -> None:
    engine = _current_engine(tmp_path / "legacy.db")
    _downgrade_identifiers_to_pre_domain(engine)
    ids = _seed_evidence_graph(engine)
    before = _snapshot(engine)

    assert migrate_sqlite_schema(engine) is True
    assert _snapshot(engine) == before
    assert migrate_sqlite_schema(engine) is False

    with engine.begin() as connection:
        assert connection.exec_driver_sql("PRAGMA foreign_key_check").all() == []
        observation_identifier = connection.exec_driver_sql(
            "SELECT identifier_id FROM observations WHERE id=?",
            (ids["observation"],),
        ).scalar_one()
        assert observation_identifier == ids["identifier"]

        connection.exec_driver_sql(
            "INSERT INTO identifiers(id, subject_id, kind, raw_value, normalized_value, "
            "comparison_key, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                uuid4().hex,
                ids["subject"],
                "domain",
                "example.com",
                "example.com",
                "example.com",
                "2026-08-20 00:00:01.000000",
            ),
        )
        with pytest.raises(IntegrityError):
            connection.exec_driver_sql(
                "INSERT INTO identifiers(id, subject_id, kind, raw_value, normalized_value, "
                "comparison_key, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    uuid4().hex,
                    ids["subject"],
                    "unsupported",
                    "x",
                    "x",
                    "x",
                    "2026-08-20 00:00:02.000000",
                ),
            )


def test_unknown_identifier_constraint_fails_closed(tmp_path: Path) -> None:
    engine = _current_engine(tmp_path / "unknown.db")
    _downgrade_identifiers_to_pre_domain(engine)

    raw = engine.raw_connection()
    cursor = raw.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=OFF")
        cursor.execute("PRAGMA writable_schema=ON")
        sql = cursor.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='identifiers'"
        ).fetchone()[0]
        cursor.execute(
            "UPDATE sqlite_master SET sql=? WHERE type='table' AND name='identifiers'",
            (sql.replace("'organization'", "'organization', 'mystery'"),),
        )
        raw.commit()
    finally:
        cursor.execute("PRAGMA writable_schema=OFF")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
        raw.close()

    engine.dispose()
    engine = create_database_engine(f"sqlite+pysqlite:///{tmp_path / 'unknown.db'}")
    with pytest.raises(SQLiteSchemaMigrationError, match="Unsupported SQLite evidence schema"):
        migrate_sqlite_schema(engine)


def test_failed_rebuild_rolls_back_old_table(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = _current_engine(tmp_path / "rollback.db")
    _downgrade_identifiers_to_pre_domain(engine)
    ids = _seed_evidence_graph(engine)
    before = _snapshot(engine)

    import app.evidence.migrations as migrations

    def explode(_engine, cursor) -> None:
        cursor.execute("DROP TABLE identifiers")
        raise RuntimeError("forced migration failure")

    monkeypatch.setattr(migrations, "_rebuild_identifier_table", explode)
    with pytest.raises(RuntimeError, match="forced migration failure"):
        migrate_sqlite_schema(engine)

    assert _snapshot(engine) == before
    with engine.connect() as connection:
        assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one() == 1
        assert connection.exec_driver_sql("PRAGMA foreign_key_check").all() == []
        assert connection.exec_driver_sql(
            "SELECT id FROM identifiers WHERE id=?",
            (ids["identifier"],),
        ).scalar_one() == ids["identifier"]


def test_create_schema_keeps_new_sqlite_database_current(tmp_path: Path) -> None:
    from app.evidence import create_schema

    engine = create_database_engine(f"sqlite+pysqlite:///{tmp_path / 'new.db'}")
    create_schema(engine)
    create_schema(engine)

    with engine.connect() as connection:
        identifier_sql = connection.exec_driver_sql(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='identifiers'"
        ).scalar_one()
        assert "'domain'" in identifier_sql
        assert connection.exec_driver_sql("PRAGMA foreign_key_check").all() == []
