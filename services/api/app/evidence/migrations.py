# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy import Engine, MetaData
from sqlalchemy.schema import CreateIndex, CreateTable

from .models import Identifier, Subject
from .types import IdentifierKind

SQLITE_DOMAIN_IDENTIFIER_MIGRATION = "2026-08-20-domain-identifier-kind-v1"
_TEMP_IDENTIFIERS = "identifiers__pl_domain_migration"
_IDENTIFIER_COLUMNS = (
    "id",
    "subject_id",
    "kind",
    "raw_value",
    "normalized_value",
    "comparison_key",
    "created_at",
)
_KIND_CHECK_RE = re.compile(
    r"CHECK\s*\(\s*[\"`\[]?kind[\"`\]]?\s+IN\s*\((?P<values>[^)]*)\)\s*\)",
    re.IGNORECASE | re.DOTALL,
)
_QUOTED_VALUE_RE = re.compile(r"'((?:''|[^'])*)'")


class SQLiteSchemaMigrationError(RuntimeError):
    """Raised when an on-disk SQLite schema cannot be migrated safely."""


@dataclass(frozen=True)
class _IdentifierSchema:
    kind_values: frozenset[str]


def migrate_sqlite_schema(engine: Engine) -> bool:
    """Migrate the known pre-DOMAIN SQLite identifier constraint in place.

    The migration is deliberately narrow. Unknown identifier-table shapes fail closed
    rather than being rebuilt speculatively. The table replacement runs in one SQLite
    transaction with foreign-key verification before commit.
    """
    if engine.dialect.name != "sqlite":
        return False

    raw = engine.raw_connection()
    cursor = raw.cursor()
    try:
        table_sql = _table_sql(cursor, "identifiers")
        if table_sql is None:
            return False

        schema = _inspect_identifier_schema(table_sql)
        _validate_identifier_structure(cursor)
        if _table_sql(cursor, _TEMP_IDENTIFIERS) is not None:
            raise SQLiteSchemaMigrationError(
                "SQLite evidence migration found a reserved temporary table. Back up the "
                "database and remove only a confirmed failed PersonaLattice migration "
                "artifact before retrying."
            )

        current_values = frozenset(item.value for item in IdentifierKind)
        legacy_values = current_values - {IdentifierKind.DOMAIN.value}

        if schema.kind_values == current_values:
            return False
        if schema.kind_values != legacy_values:
            raise SQLiteSchemaMigrationError(
                "Unsupported SQLite evidence schema: identifiers.kind does not match "
                "the known pre-DOMAIN or current constraint. Back up the database and "
                "upgrade from a supported PersonaLattice schema."
            )
    finally:
        cursor.close()
        raw.close()

    raw = engine.raw_connection()
    cursor = raw.cursor()
    previous_legacy_alter_table: int | None = None
    foreign_keys = 1
    try:
        foreign_keys = int(cursor.execute("PRAGMA foreign_keys").fetchone()[0])
        previous_legacy_alter_table = int(
            cursor.execute("PRAGMA legacy_alter_table").fetchone()[0]
        )
        if raw.in_transaction:
            raw.rollback()

        cursor.execute("PRAGMA foreign_keys=OFF")
        if int(cursor.execute("PRAGMA foreign_keys").fetchone()[0]) != 0:
            raise SQLiteSchemaMigrationError(
                "SQLite evidence migration could not disable foreign-key enforcement "
                "before the atomic table rebuild."
            )

        cursor.execute("PRAGMA legacy_alter_table=ON")
        cursor.execute("BEGIN IMMEDIATE")
        try:
            _rebuild_identifier_table(engine, cursor)
            violations = cursor.execute("PRAGMA foreign_key_check").fetchall()
            if violations:
                raise SQLiteSchemaMigrationError(
                    "SQLite evidence migration found foreign-key violations and was rolled back."
                )
            raw.commit()
        except Exception:
            raw.rollback()
            raise
    finally:
        try:
            if previous_legacy_alter_table is not None:
                cursor.execute(
                    f"PRAGMA legacy_alter_table={1 if previous_legacy_alter_table else 0}"
                )
            cursor.execute(f"PRAGMA foreign_keys={1 if foreign_keys else 0}")
        finally:
            cursor.close()
            raw.close()

    return True


def _table_sql(cursor, table_name: str) -> str | None:
    row = cursor.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    return None if row is None else row[0]


def _inspect_identifier_schema(table_sql: str) -> _IdentifierSchema:
    match = _KIND_CHECK_RE.search(table_sql)
    if match is None:
        raise SQLiteSchemaMigrationError(
            "Unsupported SQLite evidence schema: identifiers.kind CHECK constraint is missing."
        )

    values = frozenset(
        value.replace("''", "'")
        for value in _QUOTED_VALUE_RE.findall(match.group("values"))
    )
    if not values:
        raise SQLiteSchemaMigrationError(
            "Unsupported SQLite evidence schema: identifiers.kind CHECK constraint is unreadable."
        )
    return _IdentifierSchema(kind_values=values)


def _validate_identifier_structure(cursor) -> None:
    columns = cursor.execute("PRAGMA table_info('identifiers')").fetchall()
    column_names = tuple(row[1] for row in columns)
    if column_names != _IDENTIFIER_COLUMNS:
        raise SQLiteSchemaMigrationError(
            "Unsupported SQLite evidence schema: identifiers columns do not match the known layout."
        )

    subject_fk = [
        row
        for row in cursor.execute("PRAGMA foreign_key_list('identifiers')").fetchall()
        if row[3] == "subject_id"
    ]
    if len(subject_fk) != 1 or subject_fk[0][2] != "subjects" or subject_fk[0][4] != "id":
        raise SQLiteSchemaMigrationError(
            "Unsupported SQLite evidence schema: identifiers.subject_id foreign key is incompatible."
        )

    unique_index_found = False
    for index_row in cursor.execute("PRAGMA index_list('identifiers')").fetchall():
        if not index_row[2]:
            continue
        index_columns = tuple(
            row[2]
            for row in cursor.execute(f"PRAGMA index_info('{index_row[1]}')").fetchall()
        )
        if index_columns == ("subject_id", "kind", "comparison_key"):
            unique_index_found = True
            break

    if not unique_index_found:
        raise SQLiteSchemaMigrationError(
            "Unsupported SQLite evidence schema: identifier uniqueness constraint is missing."
        )


def _rebuild_identifier_table(engine: Engine, cursor) -> None:
    cursor.execute(f'DROP TABLE IF EXISTS "{_TEMP_IDENTIFIERS}"')

    metadata = MetaData()
    Subject.__table__.to_metadata(metadata)
    temp_table = Identifier.__table__.to_metadata(metadata, name=_TEMP_IDENTIFIERS)
    cursor.execute(str(CreateTable(temp_table).compile(dialect=engine.dialect)))

    column_list = ", ".join(f'"{column}"' for column in _IDENTIFIER_COLUMNS)
    cursor.execute(
        f'INSERT INTO "{_TEMP_IDENTIFIERS}" ({column_list}) '
        f'SELECT {column_list} FROM "identifiers"'
    )

    old_count = int(cursor.execute('SELECT count(*) FROM "identifiers"').fetchone()[0])
    new_count = int(
        cursor.execute(f'SELECT count(*) FROM "{_TEMP_IDENTIFIERS}"').fetchone()[0]
    )
    if old_count != new_count:
        raise SQLiteSchemaMigrationError(
            "SQLite evidence migration row-count verification failed and was rolled back."
        )

    difference = cursor.execute(
        f'SELECT {column_list} FROM "identifiers" '
        f'EXCEPT SELECT {column_list} FROM "{_TEMP_IDENTIFIERS}" LIMIT 1'
    ).fetchone()
    reverse_difference = cursor.execute(
        f'SELECT {column_list} FROM "{_TEMP_IDENTIFIERS}" '
        f'EXCEPT SELECT {column_list} FROM "identifiers" LIMIT 1'
    ).fetchone()
    if difference is not None or reverse_difference is not None:
        raise SQLiteSchemaMigrationError(
            "SQLite evidence migration content verification failed and was rolled back."
        )

    cursor.execute('DROP TABLE "identifiers"')
    cursor.execute(f'ALTER TABLE "{_TEMP_IDENTIFIERS}" RENAME TO "identifiers"')
    for index in Identifier.__table__.indexes:
        cursor.execute(str(CreateIndex(index).compile(dialect=engine.dialect)))
