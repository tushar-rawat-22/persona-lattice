# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json

import pytest

from app.admin_auth import hash_admin_password
from app.launch_preflight import LaunchPreflightError, run_launch_preflight


def _safe_env(tmp_path) -> dict[str, str]:
    return {
        "PERSONALATTICE_ADMIN_USERNAME": "operator",
        "PERSONALATTICE_ADMIN_PASSWORD_HASH": hash_admin_password("ci-launch-password-123"),
        "PERSONALATTICE_COOKIE_SECURE": "true",
        "PERSONALATTICE_DB_PATH": str(tmp_path / "personalattice.db"),
        "PERSONALATTICE_CASE_RETENTION_DAYS": "30",
        "PERSONALATTICE_API_ORIGIN": "http://127.0.0.1:8000",
    }


def test_launch_preflight_accepts_zero_spend_production_shape(tmp_path) -> None:
    report = run_launch_preflight(_safe_env(tmp_path))

    assert report.cookie_name == "__Host-personalattice_session"
    assert report.database_path == str(tmp_path / "personalattice.db")
    assert report.retention_days == 30
    assert report.api_origin == "http://127.0.0.1:8000"
    assert report.configured_optional_integrations == ()


def test_launch_preflight_never_serializes_provider_secret_values(tmp_path) -> None:
    env = _safe_env(tmp_path)
    env["OPENALEX_API_KEY"] = "do-not-print-openalex-secret"
    env["COMPANIES_HOUSE_API_KEY"] = "do-not-print-companies-house-secret"

    rendered = json.dumps(run_launch_preflight(env).as_dict(), sort_keys=True)

    assert "do-not-print-openalex-secret" not in rendered
    assert "do-not-print-companies-house-secret" not in rendered
    assert "openalex" in rendered
    assert "companies_house" in rendered


@pytest.mark.parametrize(
    ("key", "value", "message"),
    [
        ("PERSONALATTICE_COOKIE_SECURE", "false", "COOKIE_SECURE"),
        ("PERSONALATTICE_DB_PATH", "relative.db", "must be absolute"),
        ("PERSONALATTICE_DB_PATH", ":memory:", "cannot be in-memory"),
        ("PERSONALATTICE_CASE_RETENTION_DAYS", "0", "between 1 and 365"),
        ("PERSONALATTICE_API_ORIGIN", "https://api.example.test:443", "loopback HTTP"),
    ],
)
def test_launch_preflight_rejects_unsafe_production_settings(
    tmp_path,
    key: str,
    value: str,
    message: str,
) -> None:
    env = _safe_env(tmp_path)
    env[key] = value

    with pytest.raises(LaunchPreflightError, match=message):
        run_launch_preflight(env)


def test_launch_preflight_rejects_non_host_cookie(tmp_path) -> None:
    env = _safe_env(tmp_path)
    env["PERSONALATTICE_SESSION_COOKIE"] = "personalattice_session"

    with pytest.raises(LaunchPreflightError, match="__Host-"):
        run_launch_preflight(env)


def test_launch_preflight_rejects_invalid_argon2_hash(tmp_path) -> None:
    env = _safe_env(tmp_path)
    env["PERSONALATTICE_ADMIN_PASSWORD_HASH"] = "not-a-password-hash"

    with pytest.raises(LaunchPreflightError, match="valid Argon2"):
        run_launch_preflight(env)


def test_launch_preflight_rejects_conflicting_api_proxy_settings(tmp_path) -> None:
    env = _safe_env(tmp_path)
    env["PERSONALATTICE_API_HOSTPORT"] = "127.0.0.1:8000"

    with pytest.raises(LaunchPreflightError, match="only PERSONALATTICE_API_ORIGIN"):
        run_launch_preflight(env)
