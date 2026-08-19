# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from datetime import date

import pytest

from app.providers.errors import ProviderPolicyError
from app.providers.webfinger_host_policy import (
    WEBFINGER_HOST_POLICIES,
    WebFingerHostPolicy,
    webfinger_host_policy_for,
)


def _policy(hostname: str = "social.example") -> WebFingerHostPolicy:
    return WebFingerHostPolicy(
        hostname=hostname,
        reviewed_on=date(2026, 8, 1),
        review_expires_on=date(2026, 9, 1),
        rationale="Fixture host with an explicit current source-policy review.",
    )


def test_production_webfinger_host_policy_is_empty_until_a_real_host_is_reviewed() -> None:
    assert WEBFINGER_HOST_POLICIES == ()
    with pytest.raises(ProviderPolicyError, match="no current exact-host"):
        webfinger_host_policy_for(
            "https://social.example/@alice",
            on_date=date(2026, 8, 19),
        )


def test_exact_reviewed_host_is_admitted_without_widening_to_subdomains() -> None:
    policy = _policy()
    assert (
        webfinger_host_policy_for(
            "https://social.example/@alice",
            on_date=date(2026, 8, 19),
            policies=(policy,),
        )
        is policy
    )

    with pytest.raises(ProviderPolicyError, match="no current exact-host"):
        webfinger_host_policy_for(
            "https://people.social.example/@alice",
            on_date=date(2026, 8, 19),
            policies=(policy,),
        )


def test_expired_or_not_yet_effective_host_review_fails_closed() -> None:
    policy = _policy()
    with pytest.raises(ProviderPolicyError, match="future"):
        webfinger_host_policy_for(
            "https://social.example/@alice",
            on_date=date(2026, 7, 31),
            policies=(policy,),
        )
    with pytest.raises(ProviderPolicyError, match="expired"):
        webfinger_host_policy_for(
            "https://social.example/@alice",
            on_date=date(2026, 9, 2),
            policies=(policy,),
        )


def test_duplicate_exact_host_approvals_fail_closed() -> None:
    policy = _policy()
    duplicate = WebFingerHostPolicy(
        hostname="social.example",
        reviewed_on=date(2026, 8, 2),
        review_expires_on=date(2026, 9, 2),
        rationale="Second fixture approval that must never coexist.",
    )
    with pytest.raises(ProviderPolicyError, match="duplicate exact-host"):
        webfinger_host_policy_for(
            "https://social.example/@alice",
            on_date=date(2026, 8, 19),
            policies=(policy, duplicate),
        )


def test_host_policy_rejects_wildcards_and_empty_rationale() -> None:
    with pytest.raises(ValueError, match="wildcard"):
        WebFingerHostPolicy(
            hostname="*.example",
            reviewed_on=date(2026, 8, 1),
            review_expires_on=date(2026, 9, 1),
            rationale="Not allowed.",
        )
    with pytest.raises(ValueError, match="rationale"):
        WebFingerHostPolicy(
            hostname="social.example",
            reviewed_on=date(2026, 8, 1),
            review_expires_on=date(2026, 9, 1),
            rationale="   ",
        )
