# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from .contracts import (
    LeadCandidate,
    LeadDisposition,
    LeadKind,
    LeadReason,
    canonicalize_lead,
)
from .graph_evaluation import PivotRelevance
from .graph_limit_evaluation import GraphFixtureLead
from .m10_cohort import M10GraphFixture


_REASON_BY_KIND = {
    LeadKind.USERNAME: LeadReason.PUBLIC_USERNAME,
    LeadKind.EMAIL: LeadReason.PUBLIC_EMAIL,
    LeadKind.PHONE: LeadReason.PUBLIC_PHONE,
    LeadKind.URL: LeadReason.PUBLIC_URL,
}


def _lead(
    kind: LeadKind,
    value: str,
    *,
    disposition: LeadDisposition = LeadDisposition.AUTO_PIVOT,
) -> LeadCandidate:
    if kind not in _REASON_BY_KIND:
        raise ValueError(f"M10 synthetic cohort does not support {kind.value!r} leads.")
    display_value, comparison_key = canonicalize_lead(kind, value)
    return LeadCandidate(
        kind=kind,
        value=display_value,
        comparison_key=comparison_key,
        reason=_REASON_BY_KIND[kind],
        disposition=disposition,
        source="m10_fixture",
        source_locator=f"fixture://{kind.value}/{comparison_key}",
        field_name=_REASON_BY_KIND[kind].value,
    )


def broadened_synthetic_m10_cohort() -> tuple[M10GraphFixture, ...]:
    """Return a deterministic multi-kind cohort for frontier-policy comparison.

    The cohort is synthetic evaluation data, not evidence that these shapes are
    representative of production research. It deliberately includes depth stops,
    duplicates, provider failures and a review-only phone lead across username,
    email, URL and phone seeds.
    """

    depth_seed = _lead(LeadKind.USERNAME, "depth-seed")
    alpha = _lead(LeadKind.USERNAME, "alpha")
    beta = _lead(LeadKind.USERNAME, "beta")
    deep_wrong = _lead(LeadKind.USERNAME, "deep-wrong")

    duplicate_seed = _lead(LeadKind.USERNAME, "duplicate-seed")
    repeated = _lead(LeadKind.USERNAME, "repeated")

    failure_seed = _lead(LeadKind.USERNAME, "failure-seed")
    failed = _lead(LeadKind.USERNAME, "failed")
    kept = _lead(LeadKind.USERNAME, "kept")

    email_seed = _lead(LeadKind.EMAIL, "analyst@example.com")
    email_url = _lead(LeadKind.URL, "https://example.com/profile")
    email_handle = _lead(LeadKind.USERNAME, "email-handle")
    email_deep_wrong = _lead(LeadKind.EMAIL, "wrong@example.net")

    url_seed = _lead(LeadKind.URL, "https://portfolio.example/profile")
    url_email = _lead(LeadKind.EMAIL, "public@example.org")
    url_failed_handle = _lead(LeadKind.USERNAME, "url-failed")
    url_phone_review = _lead(
        LeadKind.PHONE,
        "+14155552671",
        disposition=LeadDisposition.REVIEW_REQUIRED,
    )

    phone_seed = _lead(LeadKind.PHONE, "+442079460018")
    phone_handle = _lead(LeadKind.USERNAME, "phone-handle")
    phone_url_wrong = _lead(LeadKind.URL, "https://wrong.example/profile")
    phone_deep_wrong = _lead(LeadKind.EMAIL, "deep-wrong@example.net")

    return (
        M10GraphFixture(
            name="username_depth_tradeoff",
            seed_key=depth_seed.key,
            seed_kind=LeadKind.USERNAME,
            leads_by_parent={
                depth_seed.key: (GraphFixtureLead(alpha),),
                alpha.key: (GraphFixtureLead(beta),),
                beta.key: (GraphFixtureLead(deep_wrong),),
            },
            pivot_relevance_by_key={
                alpha.key: PivotRelevance.RELEVANT,
                beta.key: PivotRelevance.RELEVANT,
                deep_wrong.key: PivotRelevance.WRONG,
            },
        ),
        M10GraphFixture(
            name="username_duplicate_heavy",
            seed_key=duplicate_seed.key,
            seed_kind=LeadKind.USERNAME,
            leads_by_parent={
                duplicate_seed.key: (
                    GraphFixtureLead(repeated),
                    GraphFixtureLead(repeated),
                )
            },
            pivot_relevance_by_key={repeated.key: PivotRelevance.RELEVANT},
        ),
        M10GraphFixture(
            name="username_provider_failure",
            seed_key=failure_seed.key,
            seed_kind=LeadKind.USERNAME,
            leads_by_parent={
                failure_seed.key: (
                    GraphFixtureLead(failed, provider_fails=True),
                    GraphFixtureLead(kept),
                )
            },
            pivot_relevance_by_key={kept.key: PivotRelevance.RELEVANT},
        ),
        M10GraphFixture(
            name="email_to_url_to_username",
            seed_key=email_seed.key,
            seed_kind=LeadKind.EMAIL,
            leads_by_parent={
                email_seed.key: (GraphFixtureLead(email_url),),
                email_url.key: (GraphFixtureLead(email_handle),),
                email_handle.key: (GraphFixtureLead(email_deep_wrong),),
            },
            pivot_relevance_by_key={
                email_url.key: PivotRelevance.RELEVANT,
                email_handle.key: PivotRelevance.RELEVANT,
                email_deep_wrong.key: PivotRelevance.WRONG,
            },
        ),
        M10GraphFixture(
            name="url_duplicate_failure_and_phone_review",
            seed_key=url_seed.key,
            seed_kind=LeadKind.URL,
            leads_by_parent={
                url_seed.key: (
                    GraphFixtureLead(url_email),
                    GraphFixtureLead(url_email),
                ),
                url_email.key: (
                    GraphFixtureLead(url_failed_handle, provider_fails=True),
                    GraphFixtureLead(url_phone_review),
                ),
            },
            pivot_relevance_by_key={url_email.key: PivotRelevance.RELEVANT},
        ),
        M10GraphFixture(
            name="reviewed_phone_seed_depth_tradeoff",
            seed_key=phone_seed.key,
            seed_kind=LeadKind.PHONE,
            leads_by_parent={
                phone_seed.key: (GraphFixtureLead(phone_handle),),
                phone_handle.key: (GraphFixtureLead(phone_url_wrong),),
                phone_url_wrong.key: (GraphFixtureLead(phone_deep_wrong),),
            },
            pivot_relevance_by_key={
                phone_handle.key: PivotRelevance.RELEVANT,
                phone_url_wrong.key: PivotRelevance.WRONG,
                phone_deep_wrong.key: PivotRelevance.WRONG,
            },
        ),
    )
