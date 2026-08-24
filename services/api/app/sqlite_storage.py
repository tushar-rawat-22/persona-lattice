# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import os
from pathlib import Path
import stat


_PRIVATE_FILE_MODE = stat.S_IRUSR | stat.S_IWUSR


def private_runtime_database_path() -> Path:
    """Return the configured SQLite path after enforcing the local privacy boundary.

    Retained cases, upload-review state and audit metadata share this database.
    POSIX launch hosts must not let it inherit a permissive umask and become
    readable by other local users. The leaf is opened without following
    symbolic links when the platform supports that flag, verified as a regular
    file, and restricted through the open descriptor before SQLite receives the
    path.
    """

    raw = os.environ.get("PERSONALATTICE_DB_PATH", "./personalattice.db").strip()
    if not raw:
        raise RuntimeError("PERSONALATTICE_DB_PATH is empty.")

    path = Path(raw).expanduser()
    if path.is_symlink():
        raise RuntimeError("PERSONALATTICE_DB_PATH must not be a symbolic link.")
    path.parent.mkdir(parents=True, exist_ok=True)

    flags = os.O_RDONLY | os.O_CREAT
    flags |= getattr(os, "O_CLOEXEC", 0)
    if os.name == "posix":
        flags |= getattr(os, "O_NOFOLLOW", 0)

    try:
        descriptor = os.open(path, flags, _PRIVATE_FILE_MODE)
    except OSError as exc:
        if path.is_symlink():
            raise RuntimeError("PERSONALATTICE_DB_PATH must not be a symbolic link.") from exc
        raise RuntimeError("PersonaLattice database could not be opened securely.") from exc

    try:
        file_status = os.fstat(descriptor)
        if not stat.S_ISREG(file_status.st_mode):
            raise RuntimeError("PERSONALATTICE_DB_PATH must reference a regular file.")

        if os.name == "posix":
            try:
                os.fchmod(descriptor, _PRIVATE_FILE_MODE)
                mode = stat.S_IMODE(os.fstat(descriptor).st_mode)
            except OSError as exc:
                raise RuntimeError(
                    "PersonaLattice database permissions could not be restricted."
                ) from exc
            if mode != _PRIVATE_FILE_MODE:
                raise RuntimeError(
                    "PersonaLattice database is not restricted to the current user."
                )
    finally:
        os.close(descriptor)

    return path
