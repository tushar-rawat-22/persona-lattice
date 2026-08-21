# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import sys
from urllib.parse import urlsplit

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError

from .admin_auth import AuthConfigurationError, load_admin_auth_config


_OPTIONAL_PROVIDER_KEYS = (
    "BRAVE_SEARCH_API_KEY",
    "COMPANIES_HOUSE_API_KEY",
    "OPENALEX_API_KEY",
)
_DEFAULT_RETENTION_DAYS = 30
_MAX_RETENTION_DAYS = 365


class LaunchPreflightError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class LaunchPreflightReport:
    cookie_name: str
    database_path: str
    retention_days: int
    api_origin: str
    configured_optional_integrations: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "status": "ready",
            "cookie_name": self.cookie_name,
            "database_path": self.database_path,
            "retention_days": self.retention_days,
            "api_origin": self.api_origin,
            "configured_optional_integrations": list(self.configured_optional_integrations),
        }


def _production_api_origin(environ: dict[str, str]) -> str:
    raw_origin = environ.get("PERSONALATTICE_API_ORIGIN", "").strip()
    raw_hostport = environ.get("PERSONALATTICE_API_HOSTPORT", "").strip()
    if raw_origin and raw_hostport:
        raise LaunchPreflightError(
            "Configure only PERSONALATTICE_API_ORIGIN or PERSONALATTICE_API_HOSTPORT, not both."
        )

    origin = raw_origin or (f"http://{raw_hostport}" if raw_hostport else "http://127.0.0.1:8000")
    parsed = urlsplit(origin)
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost"}:
        raise LaunchPreflightError(
            "The production web proxy must reach the API over a loopback HTTP origin."
        )
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise LaunchPreflightError("The production API origin contains unsupported URL components.")
    if parsed.path not in {"", "/"}:
        raise LaunchPreflightError("The production API origin must not contain a path prefix.")
    if parsed.port is None:
        raise LaunchPreflightError("The production API origin must include an explicit port.")
    return f"http://{parsed.hostname}:{parsed.port}"


def _persistent_database_path(environ: dict[str, str]) -> Path:
    raw = environ.get("PERSONALATTICE_DB_PATH", "").strip()
    if not raw:
        raise LaunchPreflightError("PERSONALATTICE_DB_PATH must be set for production.")
    if raw == ":memory:":
        raise LaunchPreflightError("The production case database cannot be in-memory.")
    path = Path(raw).expanduser()
    if not path.is_absolute():
        raise LaunchPreflightError("PERSONALATTICE_DB_PATH must be absolute for production.")
    return path


def _retention_days(environ: dict[str, str]) -> int:
    raw = environ.get("PERSONALATTICE_CASE_RETENTION_DAYS", str(_DEFAULT_RETENTION_DAYS)).strip()
    try:
        days = int(raw)
    except ValueError as exc:
        raise LaunchPreflightError("Case retention configuration is invalid.") from exc
    if not 1 <= days <= _MAX_RETENTION_DAYS:
        raise LaunchPreflightError("Case retention must be between 1 and 365 days.")
    return days


def _validate_password_hash(password_hash: str) -> None:
    try:
        PasswordHasher().check_needs_rehash(password_hash)
    except InvalidHashError as exc:
        raise LaunchPreflightError("The configured admin password hash is not a valid Argon2 hash.") from exc


def run_launch_preflight(environ: dict[str, str] | None = None) -> LaunchPreflightReport:
    env = dict(os.environ if environ is None else environ)

    original = os.environ.copy()
    try:
        os.environ.clear()
        os.environ.update(env)
        try:
            auth = load_admin_auth_config()
        except AuthConfigurationError as exc:
            raise LaunchPreflightError(str(exc)) from exc
    finally:
        os.environ.clear()
        os.environ.update(original)

    if not auth.cookie_secure:
        raise LaunchPreflightError("Production requires PERSONALATTICE_COOKIE_SECURE=true.")
    if not auth.cookie_name.startswith("__Host-"):
        raise LaunchPreflightError("Production requires a __Host- session cookie name.")
    _validate_password_hash(auth.password_hash)

    database_path = _persistent_database_path(env)
    retention_days = _retention_days(env)
    api_origin = _production_api_origin(env)

    configured = tuple(
        name.removesuffix("_API_KEY").lower()
        for name in _OPTIONAL_PROVIDER_KEYS
        if env.get(name, "").strip()
    )

    return LaunchPreflightReport(
        cookie_name=auth.cookie_name,
        database_path=str(database_path),
        retention_days=retention_days,
        api_origin=api_origin,
        configured_optional_integrations=configured,
    )


def main() -> int:
    try:
        report = run_launch_preflight()
    except LaunchPreflightError as exc:
        print(f"launch preflight failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report.as_dict(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
