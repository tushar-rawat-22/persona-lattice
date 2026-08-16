# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from datetime import UTC, datetime

from .types import AuthorizationDecision, AuthorizationRequest, DecisionReason


class AuthorizationDenied(PermissionError):
    def __init__(self, decision: AuthorizationDecision) -> None:
        self.decision = decision
        super().__init__(decision.reason.value)


def authorize(
    request: AuthorizationRequest,
    *,
    now: datetime | None = None,
) -> AuthorizationDecision:
    """Authorize one protected operation for PersonaLattice's sole admin.

    M7 intentionally has no tenant, role or ownership hierarchy. The authentication
    adapter must first resolve an opaque server-side session into an
    AuthenticatedPrincipal. Any protected operation without that principal fails
    closed. Resource identifiers never confer authority by themselves.
    """

    principal = request.principal
    if principal is None:
        return AuthorizationDecision(False, DecisionReason.DENY_ANONYMOUS)

    evaluated_at = now or datetime.now(UTC)
    if evaluated_at.tzinfo is None:
        raise ValueError("authorization evaluation time must be timezone-aware")
    if principal.session_expires_at <= evaluated_at:
        return AuthorizationDecision(False, DecisionReason.DENY_SESSION_EXPIRED)

    return AuthorizationDecision(True, DecisionReason.ALLOW_ADMIN)


def require_authorized(
    request: AuthorizationRequest,
    *,
    now: datetime | None = None,
) -> AuthorizationDecision:
    decision = authorize(request, now=now)
    if not decision.allowed:
        raise AuthorizationDenied(decision)
    return decision
