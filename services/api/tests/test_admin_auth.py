# SPDX-License-Identifier: Apache-2.0
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException

from app.admin_auth import (
    LOGIN_THROTTLE,
    SESSION_STORE,
    authenticate_admin,
    hash_admin_password,
    load_admin_auth_config,
    verify_admin_password,
)


PASSWORD = "synthetic-admin-password-123!"
NOW = datetime(2026, 8, 16, 10, 0, tzinfo=UTC)


def _configure(monkeypatch) -> None:
    monkeypatch.setenv("PERSONALATTICE_ADMIN_USERNAME", "admin")
    monkeypatch.setenv("PERSONALATTICE_ADMIN_PASSWORD_HASH", hash_admin_password(PASSWORD))
    monkeypatch.setenv("PERSONALATTICE_COOKIE_SECURE", "false")
    monkeypatch.setenv("PERSONALATTICE_SESSION_COOKIE", "personalattice_test_session")
    monkeypatch.setenv("PERSONALATTICE_SESSION_SECONDS", "3600")
    SESSION_STORE.clear()
    LOGIN_THROTTLE.clear()


def test_argon2_password_hash_never_contains_plaintext() -> None:
    encoded = hash_admin_password(PASSWORD)
    assert encoded.startswith("$argon2id$")
    assert PASSWORD not in encoded
    assert verify_admin_password(encoded, PASSWORD) is True
    assert verify_admin_password(encoded, "wrong-password-value") is False


def test_authentication_configuration_requires_server_side_secrets(monkeypatch) -> None:
    monkeypatch.delenv("PERSONALATTICE_ADMIN_USERNAME", raising=False)
    monkeypatch.delenv("PERSONALATTICE_ADMIN_PASSWORD_HASH", raising=False)
    with pytest.raises(RuntimeError, match="not configured"):
        load_admin_auth_config()


def test_valid_admin_login_creates_opaque_server_side_session(monkeypatch) -> None:
    _configure(monkeypatch)

    login = authenticate_admin(
        "admin",
        PASSWORD,
        source_key="127.0.0.1",
        now=NOW,
    )

    assert login is not None
    assert len(login.token) >= 40
    assert login.token != str(login.principal.session_record_id)
    record = SESSION_STORE.resolve(login.token, now=NOW + timedelta(minutes=1))
    assert record is not None
    assert login.token not in record.token_hash
    assert record.id == login.principal.session_record_id


def test_wrong_password_does_not_create_session(monkeypatch) -> None:
    _configure(monkeypatch)

    login = authenticate_admin(
        "admin",
        "definitely-wrong-password",
        source_key="127.0.0.1",
        now=NOW,
    )

    assert login is None


def test_tampered_and_expired_tokens_fail_closed(monkeypatch) -> None:
    _configure(monkeypatch)
    login = authenticate_admin("admin", PASSWORD, source_key="127.0.0.1", now=NOW)
    assert login is not None

    assert SESSION_STORE.resolve(login.token + "tampered", now=NOW) is None
    assert SESSION_STORE.resolve(login.token, now=NOW + timedelta(hours=2)) is None


def test_revoked_session_fails_closed(monkeypatch) -> None:
    _configure(monkeypatch)
    login = authenticate_admin("admin", PASSWORD, source_key="127.0.0.1", now=NOW)
    assert login is not None

    SESSION_STORE.revoke(login.token, now=NOW + timedelta(minutes=1))
    assert SESSION_STORE.resolve(login.token, now=NOW + timedelta(minutes=2)) is None


def test_login_throttle_blocks_repeated_failures(monkeypatch) -> None:
    _configure(monkeypatch)

    for index in range(8):
        assert (
            authenticate_admin(
                "admin",
                f"wrong-password-{index}",
                source_key="198.51.100.10",
                now=NOW,
            )
            is None
        )

    with pytest.raises(HTTPException) as caught:
        authenticate_admin(
            "admin",
            PASSWORD,
            source_key="198.51.100.10",
            now=NOW,
        )

    assert caught.value.status_code == 429
