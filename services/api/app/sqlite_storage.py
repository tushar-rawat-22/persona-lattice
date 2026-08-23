# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import os
from pathlib import Path
import stat


_PRIVATE_FILE_MODE = stat.S_IRUSR | stat.S_IWUSR


def _enforce_private_mode(path: Path) -> None:
    if os.name != "posix":
        return
    try:
        os.chmod(path, _PRIVATE_FILE_MODE)
        mode = stat.S_IMODE(path.stat().st_mode)
    except OSError as exc:
        raise RuntimeError("PersonaLattice database permissions could not be restricted.") from exc
    if mode != _PRIVATE_FILE_MODE:
        raise RuntimeError("PersonaLattice database is not restricted to the current user.")


def private_runtime_database_path() -> Path:
    """Return the configured SQLite path after enforcing the local privacy boundary.

    The retained case, upload-review and audit tables share this database. On
    POSIX launch hosts it must not inherit a permissive process umask and become
    readable by other local users. Existing databases are tightened on access;
    new databases are reserved with owner-only permissions before SQLite opens
    them. A leaf symlink is rejected so configuration cannot silently redirect
    the retained-data file through a link.
    """

    raw = os.environ.get("PERSONALATTICE_DB_PATH", "./personalattice.db").strip()
    if not raw:
        raise RuntimeError("PERSONALATTICE_DB_PATH is empty.")

    path = Path(raw).expanduser()
    if path.is_symlink():
        raise RuntimeError("PERSONALATTICE_DB_PATH must not be a symbolic link.")
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        if not path.is_file():
            raise RuntimeError("PERSONALATTICE_DB_PATH must reference a regular file.")
    else:
        flags = os.O_RDWR | os.O_CREAT | os.O_EXCL
        try:
            descriptor = os.open(path, flags, _PRIVATE_FILE_MODE)
        except FileExistsError:
            if path.is_symlink() or not path.is_file():
                raise RuntimeError("PERSONALATTICE_DB_PATH changed during secure creation.")
        except OSError as exc:
            raise RuntimeError("PersonaLattice database could not be created securely.") from exc
        else:
            permission_error: OSError | None = None
            try:
                if os.name == "posix":
                    os.fchmod(descriptor, _PRIVATE_FILE_MODE)
            except OSError as exc:
                permission_error = exc
            finally:
                os.close(descriptor)
            if permission_error is not None:
                path.unlink(missing_ok=True)
                raise RuntimeError(
                    "PersonaLattice database permissions could not be restricted."
                ) from permission_error

    _enforce_private_mode(path)
    return path
