# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from getpass import getpass
import sys

from .admin_auth import hash_admin_password


def main() -> int:
    print("PersonaLattice admin password setup")
    print("The plaintext password is not written to disk by this helper.")
    first = getpass("New admin password: ")
    second = getpass("Confirm admin password: ")
    if first != second:
        print("Passwords do not match.", file=sys.stderr)
        return 2
    try:
        encoded = hash_admin_password(first)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print("\nSet this value as PERSONALATTICE_ADMIN_PASSWORD_HASH in your secret store:")
    print(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
