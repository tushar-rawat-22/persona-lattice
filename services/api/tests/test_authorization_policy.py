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
    Role,
    TenantMembership,
    authorize,
    require_authorized,
)


NOW = datetime(2026, 8, 16, 10, 30, tzinfo=UTC)


def principal(*, subject_id=None, tenant_id=None, role=Role.MEMBER, expired=False):
    return AuthenticatedPrincipal(
        subject_id=subject_id or uuid4(),
        session_record_id=uuid4(),
        session_expires_at=NOW + (timedelta(minutes=-1) if expired else timedelta(hours=1)),
        memberships=(TenantMembership(tenant_id=tenant_id or uuid4(), role=role),),
    )


def resource(*, tenant_id, owner_subject_id, resource_type=ResourceType.CASE):
    return ResourceRef(
        resource_type=resource_type,
        resource_id=uuid4(),
        tenant_id=tenant_id,
        owner_subject_id=owner_subject_id,
    )


def request(*, principal_value, action, resource_value):
    return AuthorizationRequest(
        principal=principal_value,
        action=action,
        resource=resource_value,
    )


def test_anonymous_access_is_denied_by_default():
    tenant_id = uuid4()
    decision = authorize(
        request(
            principal_value=None,
            action=Action.READ,
            resource_value=resource(tenant_id=tenant_id, owner_subject_id=uuid4()),
        ),
        now=NOW,
    )

    assert decision.allowed is False
    assert decision.reason is DecisionReason.DENY_ANONYMOUS


def test_expired_session_is_denied_before_membership_or_ownership():
    tenant_id = uuid4()
    subject_id = uuid4()
    actor = principal(subject_id=subject_id, tenant_id=tenant_id, expired=True)

    decision = authorize(
        request(
            principal_value=actor,
            action=Action.READ,
            resource_value=resource(tenant_id=tenant_id, owner_subject_id=subject_id),
        ),
        now=NOW,
    )

    assert decision.allowed is False
    assert decision.reason is DecisionReason.DENY_SESSION_EXPIRED


@pytest.mark.parametrize("action", [Action.READ, Action.UPDATE])
def test_member_can_read_or_update_own_resource(action):
    tenant_id = uuid4()
    subject_id = uuid4()
    actor = principal(subject_id=subject_id, tenant_id=tenant_id)

    decision = authorize(
        request(
            principal_value=actor,
            action=action,
            resource_value=resource(tenant_id=tenant_id, owner_subject_id=subject_id),
        ),
        now=NOW,
    )

    assert decision.allowed is True
    assert decision.reason is DecisionReason.ALLOW_OWNER


def test_member_cannot_delete_own_resource_without_explicit_grant():
    tenant_id = uuid4()
    subject_id = uuid4()
    actor = principal(subject_id=subject_id, tenant_id=tenant_id)

    decision = authorize(
        request(
            principal_value=actor,
            action=Action.DELETE,
            resource_value=resource(tenant_id=tenant_id, owner_subject_id=subject_id),
        ),
        now=NOW,
    )

    assert decision.allowed is False
    assert decision.reason is DecisionReason.DENY_ACTION_NOT_GRANTED


def test_same_tenant_member_cannot_read_another_owners_resource():
    tenant_id = uuid4()
    actor = principal(tenant_id=tenant_id)

    decision = authorize(
        request(
            principal_value=actor,
            action=Action.READ,
            resource_value=resource(tenant_id=tenant_id, owner_subject_id=uuid4()),
        ),
        now=NOW,
    )

    assert decision.allowed is False
    assert decision.reason is DecisionReason.DENY_NOT_OWNER


def test_cross_tenant_access_is_denied_even_for_admin():
    actor_tenant = uuid4()
    resource_tenant = uuid4()
    actor = principal(tenant_id=actor_tenant, role=Role.ADMIN)

    decision = authorize(
        request(
            principal_value=actor,
            action=Action.READ,
            resource_value=resource(tenant_id=resource_tenant, owner_subject_id=uuid4()),
        ),
        now=NOW,
    )

    assert decision.allowed is False
    assert decision.reason is DecisionReason.DENY_TENANT_MEMBERSHIP


@pytest.mark.parametrize("action", [Action.READ, Action.UPDATE, Action.DELETE, Action.ADMIN])
def test_tenant_admin_has_explicit_tenant_scoped_grants(action):
    tenant_id = uuid4()
    actor = principal(tenant_id=tenant_id, role=Role.ADMIN)

    decision = authorize(
        request(
            principal_value=actor,
            action=action,
            resource_value=resource(tenant_id=tenant_id, owner_subject_id=uuid4()),
        ),
        now=NOW,
    )

    assert decision.allowed is True
    assert decision.reason is DecisionReason.ALLOW_TENANT_ADMIN


def test_member_cannot_invoke_admin_action():
    tenant_id = uuid4()
    subject_id = uuid4()
    actor = principal(subject_id=subject_id, tenant_id=tenant_id)

    decision = authorize(
        request(
            principal_value=actor,
            action=Action.ADMIN,
            resource_value=resource(tenant_id=tenant_id, owner_subject_id=subject_id),
        ),
        now=NOW,
    )

    assert decision.allowed is False
    assert decision.reason is DecisionReason.DENY_ACTION_NOT_GRANTED


def test_require_authorized_raises_with_structured_denial_reason():
    tenant_id = uuid4()
    actor = principal(tenant_id=tenant_id)
    auth_request = request(
        principal_value=actor,
        action=Action.READ,
        resource_value=resource(tenant_id=tenant_id, owner_subject_id=uuid4()),
    )

    with pytest.raises(AuthorizationDenied) as exc_info:
        require_authorized(auth_request, now=NOW)

    assert exc_info.value.decision.reason is DecisionReason.DENY_NOT_OWNER


def test_principal_uses_internal_session_record_not_bearer_secret():
    actor = principal()

    assert isinstance(actor.session_record_id, type(uuid4()))
    assert not hasattr(actor, "session_id")


def test_principal_rejects_duplicate_tenant_memberships():
    tenant_id = uuid4()

    with pytest.raises(ValueError, match="duplicate tenant memberships"):
        AuthenticatedPrincipal(
            subject_id=uuid4(),
            session_record_id=uuid4(),
            session_expires_at=NOW + timedelta(hours=1),
            memberships=(
                TenantMembership(tenant_id=tenant_id, role=Role.MEMBER),
                TenantMembership(tenant_id=tenant_id, role=Role.ADMIN),
            ),
        )


def test_authorization_requires_timezone_aware_evaluation_time():
    tenant_id = uuid4()
    subject_id = uuid4()
    actor = principal(subject_id=subject_id, tenant_id=tenant_id)
    auth_request = request(
        principal_value=actor,
        action=Action.READ,
        resource_value=resource(tenant_id=tenant_id, owner_subject_id=subject_id),
    )

    with pytest.raises(ValueError, match="timezone-aware"):
        authorize(auth_request, now=datetime(2026, 8, 16, 10, 30))
