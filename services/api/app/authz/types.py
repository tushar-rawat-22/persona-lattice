# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class ResourceType(StrEnum):
    CASE = "case"
    EVIDENCE = "evidence"
    CLAIM = "claim"
    CORRELATION = "correlation"
    INTAKE = "intake"
    PROVIDER_EXECUTION = "provider_execution"
    EXPORT = "export"


class Action(StrEnum):
    READ = "read"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    EXPORT = "export"


class DecisionReason(StrEnum):
    ALLOW_ADMIN = "allow_admin"
    DENY_ANONYMOUS = "deny_anonymous"
    DENY_SESSION_EXPIRED = "deny_session_expired"


@dataclass(frozen=True, slots=True)
class AuthenticatedPrincipal:
    """Server-derived single-admin identity passed to protected services.

    The browser session secret is deliberately absent. The authentication adapter
    resolves the opaque cookie to this principal and only then invokes authorization.
    """

    session_record_id: UUID
    session_expires_at: datetime

    def __post_init__(self) -> None:
        if self.session_expires_at.tzinfo is None:
            raise ValueError("session_expires_at must be timezone-aware")


@dataclass(frozen=True, slots=True)
class ResourceRef:
    resource_type: ResourceType
    resource_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class AuthorizationRequest:
    principal: AuthenticatedPrincipal | None
    action: Action
    resource: ResourceRef


@dataclass(frozen=True, slots=True)
class AuthorizationDecision:
    allowed: bool
    reason: DecisionReason
