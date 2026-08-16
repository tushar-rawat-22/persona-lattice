# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from getpass import getpass
import secrets

from .admin_auth import hash_admin_password


def main() -> int:
    """Prompt locally for the deployment password and print only its Argon2 hash."""

    password = getpass("PersonaLattice admin password: ")
    confirmation = getpass("Confirm admin password: ")
    if not secrets.compare_digest(password, confirmation):
        print("Passwords do not match.")
        return 2

    try:
        password_hash = hash_admin_password(password)
    except ValueError as exc:
        print(str(exc))
        return 2

    print(password_hash)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
