# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import argparse
from pathlib import Path
import sqlite3
import sys


class DatabaseBackupError(RuntimeError):
    pass


def backup_sqlite_database(source: Path, destination: Path) -> None:
    source = source.expanduser().resolve()
    destination = destination.expanduser().resolve()

    if source == destination:
        raise DatabaseBackupError("Backup destination must differ from the source database.")
    if not source.is_file():
        raise DatabaseBackupError("Source database does not exist.")
    if destination.exists():
        raise DatabaseBackupError("Backup destination already exists; refusing to overwrite it.")

    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with sqlite3.connect(source, timeout=10.0) as source_connection:
            source_connection.execute("PRAGMA busy_timeout = 10000")
            with sqlite3.connect(destination, timeout=10.0) as destination_connection:
                source_connection.backup(destination_connection)
                integrity = destination_connection.execute("PRAGMA integrity_check").fetchone()
                if integrity is None or integrity[0] != "ok":
                    raise DatabaseBackupError("SQLite integrity check failed for the backup.")
    except DatabaseBackupError:
        destination.unlink(missing_ok=True)
        raise
    except sqlite3.Error as exc:
        destination.unlink(missing_ok=True)
        raise DatabaseBackupError("SQLite backup failed.") from exc


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create a verified SQLite snapshot for PersonaLattice retained data.",
    )
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        backup_sqlite_database(args.source, args.destination)
    except DatabaseBackupError as exc:
        print(f"database backup failed: {exc}", file=sys.stderr)
        return 1
    print(f"database backup verified: {args.destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
