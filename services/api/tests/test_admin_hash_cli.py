# SPDX-License-Identifier: Apache-2.0
from app import admin_hash_cli
from app.admin_auth import verify_admin_password


def test_admin_hash_cli_prints_only_hash_for_matching_passwords(monkeypatch, capsys) -> None:
    supplied = iter(["synthetic-admin-password-123!", "synthetic-admin-password-123!"])
    monkeypatch.setattr(admin_hash_cli, "getpass", lambda _prompt: next(supplied))

    assert admin_hash_cli.main() == 0
    output = capsys.readouterr().out.strip()

    assert output.startswith("$argon2")
    assert "synthetic-admin-password-123!" not in output
    assert verify_admin_password(output, "synthetic-admin-password-123!") is True


def test_admin_hash_cli_rejects_mismatch_without_hash(monkeypatch, capsys) -> None:
    supplied = iter(["synthetic-admin-password-123!", "different-password-456!"])
    monkeypatch.setattr(admin_hash_cli, "getpass", lambda _prompt: next(supplied))

    assert admin_hash_cli.main() == 2
    output = capsys.readouterr().out.strip()

    assert output == "Passwords do not match."
    assert "$argon2" not in output
