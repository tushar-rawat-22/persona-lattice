# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from datetime import UTC, datetime

from .types import (
    Action,
    AuthorizationDecision,
    AuthorizationRequest,
    DecisionReason,
    Role,
)


_OWNER_ACTIONS = {Action.READ, Action.UPDATE}
_ADMIN_ACTIONS = {Action.READ, Action.UPDATE, Action.DELETE, Action.ADMIN}


class AuthorizationDenied(PermissionError):
    def __init__(self, decision: AuthorizationDecision) -> None:
        self.decision = decision
        super().__init__(decision.reason.value)


def authorize(
    request: AuthorizationRequest,
    *,
    now: datetime | None = None,
) -> AuthorizationDecision:
    principal = request.principal
    if principal is None:
        return AuthorizationDecision(False, DecisionReason.DENY_ANONYMOUS)

    evaluated_at = now or datetime.now(UTC)
    if evaluated_at.tzinfo is None:
        raise ValueError("authorization evaluation time must be timezone-aware")
    if principal.session_expires_at <= evaluated_at:
        return AuthorizationDecision(False, DecisionReason.DENY_SESSION_EXPIRED)

    membership = principal.membership_for(request.resource.tenant_id)
    if membership is None:
        return AuthorizationDecision(False, DecisionReason.DENY_TENANT_MEMBERSHIP)

    if membership.role is Role.ADMIN:
        if request.action in _ADMIN_ACTIONS:
            return AuthorizationDecision(True, DecisionReason.ALLOW_TENANT_ADMIN)
        return AuthorizationDecision(False, DecisionReason.DENY_ACTION_NOT_GRANTED)

    if request.resource.owner_subject_id != principal.subject_id:
        return AuthorizationDecision(False, DecisionReason.DENY_NOT_OWNER)

    if request.action in _OWNER_ACTIONS:
        return AuthorizationDecision(True, DecisionReason.ALLOW_OWNER)

    return AuthorizationDecision(False, DecisionReason.DENY_ACTION_NOT_GRANTED)


def require_authorized(
    request: AuthorizationRequest,
    *,
    now: datetime | None = None,
) -> AuthorizationDecision:
    decision = authorize(request, now=now)
    if not decision.allowed:
        raise AuthorizationDenied(decision)
    return decision
