# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import pytest

from app.intelligence.contracts import (
    LeadCandidate,
    LeadDisposition,
    LeadKind,
    LeadReason,
    canonicalize_lead,
)
from app.intelligence.graph_limit_evaluation import GraphFixtureLead


def _username_lead(value: str) -> LeadCandidate:
    display_value, comparison_key = canonicalize_lead(LeadKind.USERNAME, value)
    return LeadCandidate(
        kind=LeadKind.USERNAME,
        value=display_value,
        comparison_key=comparison_key,
        reason=LeadReason.PUBLIC_USERNAME,
        disposition=LeadDisposition.AUTO_PIVOT,
        source="synthetic_graph_fixture",
        source_locator=f"fixture://{comparison_key}",
        field_name="public_username",
    )


def test_fixture_actual_result_key_must_keep_candidate_kind() -> None:
    with pytest.raises(ValueError, match="kind must match"):
        GraphFixtureLead(_username_lead("alpha"), actual_key="email:alpha@example.test")


def test_failed_fixture_provider_cannot_also_declare_result_key() -> None:
    with pytest.raises(ValueError, match="cannot also declare"):
        GraphFixtureLead(
            _username_lead("alpha"),
            provider_fails=True,
            actual_key="username:alpha",
        )
