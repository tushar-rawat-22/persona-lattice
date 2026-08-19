# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any

from .graph_limit_evaluation import GraphLimitScenario
from .m10_cohort import M10CohortComparison, M10GraphFixture, compare_m10_graph_fixture_cohort

_REPLAY_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class M10ReplayRecord:
    """Versioned digests for one deterministic M10 cohort comparison."""

    schema_version: int
    input_digest: str
    result_digest: str
    comparison: M10CohortComparison


def _sha256_json(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _candidate_payload(candidate) -> dict[str, object]:
    return {
        "kind": candidate.kind.value,
        "value": candidate.value,
        "comparison_key": candidate.comparison_key,
        "reason": candidate.reason.value,
        "disposition": candidate.disposition.value,
        "source": candidate.source,
        "source_locator": candidate.source_locator,
        "field_name": candidate.field_name,
    }


def _fixture_payload(fixture: M10GraphFixture) -> dict[str, object]:
    return {
        "name": fixture.name,
        "seed_key": fixture.seed_key,
        "seed_kind": fixture.seed_kind.value,
        "leads_by_parent": [
            {
                "parent_key": parent_key,
                "leads": [
                    {
                        "candidate": _candidate_payload(lead.candidate),
                        "provider_fails": lead.provider_fails,
                        "actual_key": lead.actual_key,
                    }
                    for lead in fixture.leads_by_parent[parent_key]
                ],
            }
            for parent_key in sorted(fixture.leads_by_parent)
        ],
        "pivot_relevance_by_key": [
            [key, fixture.pivot_relevance_by_key[key].value]
            for key in sorted(fixture.pivot_relevance_by_key)
        ],
    }


def _scenario_payload(scenario: GraphLimitScenario) -> dict[str, object]:
    return {
        "name": scenario.name,
        "limits": asdict(scenario.limits),
    }


def _comparison_payload(comparison: M10CohortComparison) -> dict[str, object]:
    return {
        "baseline": {
            "scenario": _scenario_payload(comparison.baseline.scenario),
            "counters": asdict(comparison.baseline.counters),
        },
        "candidates": [
            {
                "scenario": _scenario_payload(result.scenario),
                "counters": asdict(result.counters),
            }
            for result in comparison.candidates
        ],
        "deltas": [asdict(delta) for delta in comparison.deltas],
    }


def build_m10_replay_record(
    *,
    fixtures,
    baseline: GraphLimitScenario,
    candidates=(),
) -> M10ReplayRecord:
    """Evaluate a cohort and return deterministic input/result replay digests.

    Top-level fixture and candidate-scenario ordering is canonicalized because it
    does not change cohort semantics. Lead ordering under a fixture parent is
    preserved because it can change frontier admission and therefore is part of
    the experiment definition.
    """

    fixture_tuple = tuple(sorted(tuple(fixtures), key=lambda fixture: fixture.name))
    candidate_tuple = tuple(sorted(tuple(candidates), key=lambda scenario: scenario.name))
    comparison = compare_m10_graph_fixture_cohort(
        fixtures=fixture_tuple,
        baseline=baseline,
        candidates=candidate_tuple,
    )
    input_payload = {
        "schema_version": _REPLAY_SCHEMA_VERSION,
        "fixtures": [_fixture_payload(fixture) for fixture in fixture_tuple],
        "baseline": _scenario_payload(baseline),
        "candidates": [_scenario_payload(scenario) for scenario in candidate_tuple],
    }
    result_payload = {
        "schema_version": _REPLAY_SCHEMA_VERSION,
        "comparison": _comparison_payload(comparison),
    }
    return M10ReplayRecord(
        schema_version=_REPLAY_SCHEMA_VERSION,
        input_digest=_sha256_json(input_payload),
        result_digest=_sha256_json(result_payload),
        comparison=comparison,
    )
