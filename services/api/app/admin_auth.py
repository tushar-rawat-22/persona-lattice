# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from hashlib import sha256
import os
import secrets
from threading import BoundedSemaphore, RLock
from time import sleep
from uuid import UUID, uuid4

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from fastapi import HTTPException, Request, Response, status

from .authz import AuthenticatedPrincipal


_PASSWORD_HASHER = PasswordHasher()
_DEFAULT_SESSION_SECONDS = 8 * 60 * 60
_MAX_SESSION_SECONDS = 24 * 60 * 60
_LOGIN_WINDOW_SECONDS = 15 * 60
_LOGIN_SOFT_THRESHOLD = 3
_LOGIN_MAX_DELAY_SECONDS = 2.0
_LOGIN_VERIFY_SEMAPHORE = BoundedSemaphore(value=2)
_CSRF_HEADER = "X-PersonaLattice-CSRF"


class AuthConfigurationError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class AdminAuthConfig:
    username: str
    password_hash: str
    session_seconds: int
    cookie_secure: bool
    cookie_name: str


@dataclass(frozen=True, slots=True)
class SessionRecord:
    id: UUID
    token_hash: str
    csrf_token: str
    created_at: datetime
    expires_at: datetime
    revoked_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class LoginResult:
    token: str
    csrf_token: str
    principal: AuthenticatedPrincipal
    cookie_name: str
    cookie_secure: bool
    max_age: int


def _parse_bool(value: str | None, *, default: bool) -> bool:
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise AuthConfigurationError("Boolean authentication configuration is invalid.")


def load_admin_auth_config() -> AdminAuthConfig:
    username = os.environ.get("PERSONALATTICE_ADMIN_USERNAME", "").strip()
    password_hash = os.environ.get("PERSONALATTICE_ADMIN_PASSWORD_HASH", "").strip()
    if not username or not password_hash:
        raise AuthConfigurationError("Admin authentication is not configured.")

    raw_ttl = os.environ.get("PERSONALATTICE_SESSION_SECONDS", str(_DEFAULT_SESSION_SECONDS))
    try:
        session_seconds = int(raw_ttl)
    except ValueError as exc:
        raise AuthConfigurationError("Session duration configuration is invalid.") from exc
    if not 300 <= session_seconds <= _MAX_SESSION_SECONDS:
        raise AuthConfigurationError("Session duration is outside the supported range.")

    cookie_secure = _parse_bool(
        os.environ.get("PERSONALATTICE_COOKIE_SECURE"),
        default=True,
    )
    cookie_name = os.environ.get("PERSONALATTICE_SESSION_COOKIE", "").strip()
    if not cookie_name:
        cookie_name = "__Host-personalattice_session" if cookie_secure else "personalattice_session"
    if any(character.isspace() for character in cookie_name):
        raise AuthConfigurationError("Session cookie name is invalid.")

    return AdminAuthConfig(
        username=username,
        password_hash=password_hash,
        session_seconds=session_seconds,
        cookie_secure=cookie_secure,
        cookie_name=cookie_name,
    )


def hash_admin_password(password: str) -> str:
    if not isinstance(password, str) or len(password) < 12:
        raise ValueError("Admin password must contain at least 12 characters.")
    if len(password.encode("utf-8")) > 1024:
        raise ValueError("Admin password is too long.")
    return _PASSWORD_HASHER.hash(password)


def verify_admin_password(password_hash: str, password: str) -> bool:
    if not isinstance(password, str) or len(password.encode("utf-8")) > 1024:
        return False
    try:
        return bool(_PASSWORD_HASHER.verify(password_hash, password))
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def _token_hash(token: str) -> str:
    return sha256(token.encode("ascii")).hexdigest()


class SessionStore:
    """Fail-closed in-memory session store for the one-admin deployment.

    Only hashes of bearer session tokens are retained. CSRF tokens are independent
    random values and do not authenticate a request without the HttpOnly session
    cookie. Process restart invalidates all sessions by design.
    """

    def __init__(self) -> None:
        self._records: dict[str, SessionRecord] = {}
        self._lock = RLock()

    def create(
        self,
        *,
        lifetime_seconds: int,
        now: datetime | None = None,
    ) -> tuple[str, SessionRecord]:
        created_at = now or datetime.now(UTC)
        if created_at.tzinfo is None:
            raise ValueError("session creation time must be timezone-aware")
        token = secrets.token_urlsafe(32)
        csrf_token = secrets.token_urlsafe(32)
        record = SessionRecord(
            id=uuid4(),
            token_hash=_token_hash(token),
            csrf_token=csrf_token,
            created_at=created_at,
            expires_at=created_at + timedelta(seconds=lifetime_seconds),
        )
        with self._lock:
            self._records[record.token_hash] = record
        return token, record

    def resolve(self, token: str, *, now: datetime | None = None) -> SessionRecord | None:
        if not token:
            return None
        evaluated_at = now or datetime.now(UTC)
        if evaluated_at.tzinfo is None:
            raise ValueError("session evaluation time must be timezone-aware")
        digest = _token_hash(token)
        with self._lock:
            record = self._records.get(digest)
            if record is None or record.revoked_at is not None or record.expires_at <= evaluated_at:
                return None
            return record

    def revoke(self, token: str, *, now: datetime | None = None) -> None:
        if not token:
            return
        revoked_at = now or datetime.now(UTC)
        if revoked_at.tzinfo is None:
            raise ValueError("session revocation time must be timezone-aware")
        digest = _token_hash(token)
        with self._lock:
            record = self._records.get(digest)
            if record is not None and record.revoked_at is None:
                self._records[digest] = replace(record, revoked_at=revoked_at)

    def clear(self) -> None:
        with self._lock:
            self._records.clear()


class LoginThrottle:
    """Apply bounded delay to repeated failures without creating an admin lockout.

    The API sits behind a private-network proxy in production. A hard IP lockout
    would let an attacker who shares or controls the visible proxy source deny the
    only administrator access. Failure delay therefore slows repeated verification
    attempts but a correct password is always checked.
    """

    def __init__(self) -> None:
        self._failures: dict[str, deque[datetime]] = defaultdict(deque)
        self._lock = RLock()

    def _prune(self, key: str, now: datetime) -> deque[datetime]:
        window_start = now - timedelta(seconds=_LOGIN_WINDOW_SECONDS)
        failures = self._failures[key]
        while failures and failures[0] <= window_start:
            failures.popleft()
        return failures

    def failure(self, key: str, *, now: datetime | None = None) -> float:
        evaluated_at = now or datetime.now(UTC)
        with self._lock:
            failures = self._prune(key, evaluated_at)
            failures.append(evaluated_at)
            excess = max(0, len(failures) - _LOGIN_SOFT_THRESHOLD)
            if excess == 0:
                return 0.0
            return min(_LOGIN_MAX_DELAY_SECONDS, 0.25 * (2 ** (excess - 1)))

    def success(self, key: str) -> None:
        with self._lock:
            self._failures.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._failures.clear()


SESSION_STORE = SessionStore()
LOGIN_THROTTLE = LoginThrottle()


def authenticate_admin(
    username: str,
    password: str,
    *,
    source_key: str,
    now: datetime | None = None,
    delay_fn: Callable[[float], None] = sleep,
) -> LoginResult | None:
    config = load_admin_auth_config()
    evaluated_at = now or datetime.now(UTC)

    # Bound simultaneous Argon2 work so unauthenticated traffic cannot fan out
    # password verification across an unbounded number of worker threads.
    with _LOGIN_VERIFY_SEMAPHORE:
        username_matches = secrets.compare_digest(username, config.username)
        password_matches = verify_admin_password(config.password_hash, password)
        if not username_matches or not password_matches:
            delay = LOGIN_THROTTLE.failure(source_key, now=evaluated_at)
            if delay > 0:
                delay_fn(delay)
            return None

        LOGIN_THROTTLE.success(source_key)
        token, record = SESSION_STORE.create(
            lifetime_seconds=config.session_seconds,
            now=evaluated_at,
        )

    return LoginResult(
        token=token,
        csrf_token=record.csrf_token,
        principal=AuthenticatedPrincipal(
            session_record_id=record.id,
            session_expires_at=record.expires_at,
        ),
        cookie_name=config.cookie_name,
        cookie_secure=config.cookie_secure,
        max_age=config.session_seconds,
    )


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Admin authentication required.",
        headers={"Cache-Control": "no-store"},
    )


def _resolve_request_session(request: Request) -> tuple[AdminAuthConfig, SessionRecord]:
    try:
        config = load_admin_auth_config()
    except AuthConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin authentication is not configured.",
        ) from exc

    token = request.cookies.get(config.cookie_name, "")
    record = SESSION_STORE.resolve(token)
    if record is None:
        raise _unauthorized()
    return config, record


def require_admin(request: Request) -> AuthenticatedPrincipal:
    _config, record = _resolve_request_session(request)
    return AuthenticatedPrincipal(
        session_record_id=record.id,
        session_expires_at=record.expires_at,
    )


def require_admin_write(request: Request) -> AuthenticatedPrincipal:
    _config, record = _resolve_request_session(request)
    supplied = request.headers.get(_CSRF_HEADER, "")
    if not supplied or not secrets.compare_digest(supplied, record.csrf_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF validation failed.",
            headers={"Cache-Control": "no-store"},
        )
    return AuthenticatedPrincipal(
        session_record_id=record.id,
        session_expires_at=record.expires_at,
    )


def get_admin_session_record(request: Request) -> SessionRecord:
    _config, record = _resolve_request_session(request)
    return record


def set_admin_session_cookie(response: Response, login: LoginResult) -> None:
    response.set_cookie(
        key=login.cookie_name,
        value=login.token,
        max_age=login.max_age,
        httponly=True,
        secure=login.cookie_secure,
        samesite="strict",
        path="/",
    )
    response.headers["Cache-Control"] = "no-store"


def revoke_admin_session(request: Request, response: Response) -> None:
    try:
        config = load_admin_auth_config()
    except AuthConfigurationError:
        return
    token = request.cookies.get(config.cookie_name, "")
    SESSION_STORE.revoke(token)
    response.delete_cookie(
        key=config.cookie_name,
        path="/",
        secure=config.cookie_secure,
        httponly=True,
        samesite="strict",
    )
    response.headers["Cache-Control"] = "no-store"
