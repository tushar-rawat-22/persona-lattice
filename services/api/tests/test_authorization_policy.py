# SPDX-License-Identifier: Apache-2.0
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.authz import (
    Action,
    AuthenticatedPrincipal,
    AuthorizationDenied,
    AuthorizationRequest,
    DecisionReason,
    ResourceRef,
    ResourceType,
    authorize,
    require_authorized,
)


NOW = datetime(2026, 8, 16, 10, 0, tzinfo=UTC)


def _principal(*, expires_at: datetime | None = None) -> AuthenticatedPrincipal:
    return AuthenticatedPrincipal(
        session_record_id=uuid4(),
        session_expires_at=expires_at or NOW + timedelta(hours=1),
    )


def _request(
    principal: AuthenticatedPrincipal | None,
    *,
    action: Action = Action.READ,
    resource_type: ResourceType = ResourceType.CASE,
) -> AuthorizationRequest:
    return AuthorizationRequest(
        principal=principal,
        action=action,
        resource=ResourceRef(resource_type=resource_type, resource_id=uuid4()),
    )


def test_anonymous_access_fails_closed() -> None:
    decision = authorize(_request(None), now=NOW)
    assert decision.allowed is False
    assert decision.reason is DecisionReason.DENY_ANONYMOUS


def test_expired_session_fails_closed() -> None:
    decision = authorize(
        _request(_principal(expires_at=NOW - timedelta(seconds=1))),
        now=NOW,
    )
    assert decision.allowed is False
    assert decision.reason is DecisionReason.DENY_SESSION_EXPIRED


@pytest.mark.parametrize(
    ("action", "resource_type"),
    [
        (Action.READ, ResourceType.CASE),
        (Action.CREATE, ResourceType.INTAKE),
        (Action.EXECUTE, ResourceType.PROVIDER_EXECUTION),
        (Action.READ, ResourceType.EVIDENCE),
        (Action.EXPORT, ResourceType.EXPORT),
        (Action.DELETE, ResourceType.CASE),
    ],
)
def test_authenticated_admin_receives_explicit_protected_access(
    action: Action,
    resource_type: ResourceType,
) -> None:
    decision = authorize(
        _request(_principal(), action=action, resource_type=resource_type),
        now=NOW,
    )
    assert decision.allowed is True
    assert decision.reason is DecisionReason.ALLOW_ADMIN


def test_resource_identifier_does_not_create_anonymous_authority() -> None:
    request = AuthorizationRequest(
        principal=None,
        action=Action.READ,
        resource=ResourceRef(resource_type=ResourceType.CASE, resource_id=uuid4()),
    )
    assert authorize(request, now=NOW).allowed is False


def test_require_authorized_raises_structured_denial() -> None:
    with pytest.raises(AuthorizationDenied) as caught:
        require_authorized(_request(None), now=NOW)

    assert caught.value.decision.reason is DecisionReason.DENY_ANONYMOUS


def test_principal_requires_timezone_aware_expiry() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        AuthenticatedPrincipal(
            session_record_id=uuid4(),
            session_expires_at=datetime(2026, 8, 16, 10, 0),
        )
