# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date

from .errors import ProviderPolicyError
from .webfinger_admission import WebFingerAdmissionError, webfinger_request_target


@dataclass(frozen=True, slots=True)
class WebFingerHostPolicy:
    """Time-bounded source-policy approval for one exact WebFinger hostname."""

    hostname: str
    reviewed_on: date
    review_expires_on: date
    rationale: str

    def __post_init__(self) -> None:
        if not self.hostname or self.hostname != self.hostname.strip().lower():
            raise ValueError("WebFinger host policy hostname must be lowercase and trimmed.")
        if "*" in self.hostname:
            raise ValueError("WebFinger host policy does not permit wildcard hostnames.")
        if self.review_expires_on < self.reviewed_on:
            raise ValueError("WebFinger host policy expiry cannot precede its review date.")
        if not self.rationale.strip():
            raise ValueError("WebFinger host policy requires a concrete review rationale.")


# Deliberately empty until an exact host has a current source-policy review.
# A syntactically valid/publicly routable host is not sufficient approval.
WEBFINGER_HOST_POLICIES: tuple[WebFingerHostPolicy, ...] = ()


def webfinger_host_policy_for(
    profile_url: str,
    *,
    on_date: date | None = None,
    policies: Iterable[WebFingerHostPolicy] = WEBFINGER_HOST_POLICIES,
) -> WebFingerHostPolicy:
    """Return current exact-host approval or fail before any network execution.

    Policy lookup intentionally happens after the existing URL admission parser so
    malformed/private-target-shaped profile URLs remain ordinary admission failures.
    Host approval is exact: approving ``social.example`` never approves a sibling or
    subdomain, and approval expires until the source terms/privacy posture is reviewed
    again.
    """

    try:
        target = webfinger_request_target(profile_url)
    except WebFingerAdmissionError as exc:
        raise ProviderPolicyError(str(exc)) from exc

    current_date = on_date or date.today()
    matches = tuple(policy for policy in policies if policy.hostname == target.hostname)
    if len(matches) > 1:
        raise ProviderPolicyError("WebFinger host policy contains duplicate exact-host approvals.")
    if not matches:
        raise ProviderPolicyError(
            "WebFinger profile host has no current exact-host source-policy approval."
        )

    policy = matches[0]
    if current_date < policy.reviewed_on:
        raise ProviderPolicyError("WebFinger host policy review date is in the future.")
    if current_date > policy.review_expires_on:
        raise ProviderPolicyError("WebFinger host source-policy approval has expired.")
    return policy
