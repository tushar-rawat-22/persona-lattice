# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class Role(StrEnum):
    MEMBER = "member"
    ADMIN = "admin"


class ResourceType(StrEnum):
    CASE = "case"
    EVIDENCE = "evidence"
    CLAIM = "claim"
    CORRELATION = "correlation"


class Action(StrEnum):
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    ADMIN = "admin"


class DecisionReason(StrEnum):
    ALLOW_OWNER = "allow_owner"
    ALLOW_TENANT_ADMIN = "allow_tenant_admin"
    DENY_ANONYMOUS = "deny_anonymous"
    DENY_SESSION_EXPIRED = "deny_session_expired"
    DENY_TENANT_MEMBERSHIP = "deny_tenant_membership"
    DENY_NOT_OWNER = "deny_not_owner"
    DENY_ACTION_NOT_GRANTED = "deny_action_not_granted"


@dataclass(frozen=True, slots=True)
class TenantMembership:
    tenant_id: UUID
    role: Role


@dataclass(frozen=True, slots=True)
class AuthenticatedPrincipal:
    subject_id: UUID
    session_id: str
    session_expires_at: datetime
    memberships: tuple[TenantMembership, ...]

    def __post_init__(self) -> None:
        if not self.session_id or len(self.session_id) > 128:
            raise ValueError("session_id must be between 1 and 128 characters")
        if self.session_expires_at.tzinfo is None:
            raise ValueError("session_expires_at must be timezone-aware")
        tenant_ids = [membership.tenant_id for membership in self.memberships]
        if len(tenant_ids) != len(set(tenant_ids)):
            raise ValueError("principal cannot have duplicate tenant memberships")

    def membership_for(self, tenant_id: UUID) -> TenantMembership | None:
        return next(
            (membership for membership in self.memberships if membership.tenant_id == tenant_id),
            None,
        )


@dataclass(frozen=True, slots=True)
class ResourceRef:
    resource_type: ResourceType
    resource_id: UUID
    tenant_id: UUID
    owner_subject_id: UUID | None


@dataclass(frozen=True, slots=True)
class AuthorizationRequest:
    principal: AuthenticatedPrincipal | None
    action: Action
    resource: ResourceRef


@dataclass(frozen=True, slots=True)
class AuthorizationDecision:
    allowed: bool
    reason: DecisionReason
