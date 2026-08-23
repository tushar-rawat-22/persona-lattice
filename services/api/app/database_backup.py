# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sqlite3
import stat
import sys


class DatabaseBackupError(RuntimeError):
    pass


_PRIVATE_FILE_MODE = stat.S_IRUSR | stat.S_IWUSR


def _destination_path(path: Path) -> Path:
    """Resolve the parent without following a destination-leaf symlink."""

    requested = path.expanduser()
    if requested.is_symlink():
        raise DatabaseBackupError("Backup destination must not be a symbolic link.")
    return requested.parent.resolve() / requested.name


def _create_private_destination(path: Path) -> None:
    """Reserve a new backup path without overwriting or following a leaf symlink."""

    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    try:
        descriptor = os.open(path, flags, _PRIVATE_FILE_MODE)
    except FileExistsError as exc:
        raise DatabaseBackupError(
            "Backup destination already exists; refusing to overwrite it."
        ) from exc
    except OSError as exc:
        raise DatabaseBackupError("Backup destination could not be created securely.") from exc

    try:
        if os.name == "posix":
            os.fchmod(descriptor, _PRIVATE_FILE_MODE)
    except OSError as exc:
        raise DatabaseBackupError("Backup destination permissions could not be restricted.") from exc
    finally:
        os.close(descriptor)


def _enforce_private_permissions(path: Path) -> None:
    if os.name != "posix":
        return
    try:
        os.chmod(path, _PRIVATE_FILE_MODE)
        mode = stat.S_IMODE(path.stat().st_mode)
    except OSError as exc:
        raise DatabaseBackupError("Backup destination permissions could not be verified.") from exc
    if mode != _PRIVATE_FILE_MODE:
        raise DatabaseBackupError("Backup destination is not restricted to the current user.")


def backup_sqlite_database(source: Path, destination: Path) -> None:
    source = source.expanduser().resolve()
    destination = _destination_path(destination)

    if source == destination:
        raise DatabaseBackupError("Backup destination must differ from the source database.")
    if not source.is_file():
        raise DatabaseBackupError("Source database does not exist.")

    destination.parent.mkdir(parents=True, exist_ok=True)
    _create_private_destination(destination)
    try:
        _enforce_private_permissions(destination)
        with sqlite3.connect(source, timeout=10.0) as source_connection:
            source_connection.execute("PRAGMA busy_timeout = 10000")
            with sqlite3.connect(destination, timeout=10.0) as destination_connection:
                source_connection.backup(destination_connection)
                integrity = destination_connection.execute("PRAGMA integrity_check").fetchone()
                if integrity is None or integrity[0] != "ok":
                    raise DatabaseBackupError("SQLite integrity check failed for the backup.")
                foreign_key_violation = destination_connection.execute(
                    "PRAGMA foreign_key_check"
                ).fetchone()
                if foreign_key_violation is not None:
                    raise DatabaseBackupError("SQLite foreign-key check failed for the backup.")
        _enforce_private_permissions(destination)
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
