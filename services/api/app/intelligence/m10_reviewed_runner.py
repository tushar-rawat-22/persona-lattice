# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from .frontier import compatibility_frontier_limits
from .graph_limit_evaluation import GraphLimitScenario
from .m10_label_provenance import M10LabelBasis
from .m10_local_cohort import (
    LOCAL_COHORT_SCHEMA_VERSION,
    load_local_labelled_file,
    materialize_local_labelled_payload,
    sha256_text,
)
from .m10_replay import build_m10_replay_record
from .m10_reviewed_analysis import (
    M10ReviewedCohortAnalysis,
    build_m10_reviewed_cohort_analysis,
)


@dataclass(frozen=True, slots=True)
class M10LocalReviewedRun:
    """Privacy-bounded result of one local independently reviewed cohort."""

    schema_version: int
    cohort_name_digest: str
    local_input_digest: str
    replay_input_digest: str
    replay_result_digest: str
    label_manifest_digest: str
    analysis_digest: str
    fixture_count: int
    scenarios: tuple[dict[str, object], ...]


def _scenario_accounting_payload(
    analysis: M10ReviewedCohortAnalysis,
) -> tuple[dict[str, object], ...]:
    return tuple(asdict(scenario) for scenario in analysis.scenarios)


def evaluate_local_reviewed_payload(payload: object, *, input_digest: str) -> M10LocalReviewedRun:
    """Validate and evaluate one private reviewed cohort without retaining identifiers."""

    cohort = materialize_local_labelled_payload(
        payload,
        basis=M10LabelBasis.INDEPENDENTLY_REVIEWED,
    )
    baseline = GraphLimitScenario(
        name="production_depth_2_nodes_12",
        limits=compatibility_frontier_limits(max_depth=2, max_nodes=12),
    )
    candidate = GraphLimitScenario(
        name="candidate_depth_3_nodes_12",
        limits=compatibility_frontier_limits(max_depth=3, max_nodes=12),
    )
    replay = build_m10_replay_record(
        fixtures=cohort.fixtures,
        baseline=baseline,
        candidates=(candidate,),
    )
    analysis = build_m10_reviewed_cohort_analysis(
        fixtures=cohort.fixtures,
        replay=replay,
        provenance=cohort.provenance,
    )
    return M10LocalReviewedRun(
        schema_version=LOCAL_COHORT_SCHEMA_VERSION,
        cohort_name_digest=sha256_text(cohort.cohort_name),
        local_input_digest=input_digest,
        replay_input_digest=replay.input_digest,
        replay_result_digest=replay.result_digest,
        label_manifest_digest=analysis.label_manifest_digest,
        analysis_digest=analysis.analysis_digest,
        fixture_count=len(cohort.fixtures),
        scenarios=_scenario_accounting_payload(analysis),
    )


def evaluate_local_reviewed_file(path: Path) -> M10LocalReviewedRun:
    """Load a bounded local reviewed JSON cohort and return aggregate/digest output only."""

    payload, input_digest = load_local_labelled_file(path, label="reviewed")
    return evaluate_local_reviewed_payload(payload, input_digest=input_digest)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate a private independently reviewed M10 cohort locally. Output contains "
            "only aggregate counts and replay/provenance digests; the input file is not retained."
        )
    )
    parser.add_argument("cohort", type=Path, help="Path to a local reviewed-cohort JSON file")
    args = parser.parse_args(argv)
    try:
        result = evaluate_local_reviewed_file(args.cohort)
    except (OSError, ValueError):
        print("M10 reviewed cohort validation failed.", file=sys.stderr)
        return 2
    print(json.dumps(asdict(result), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised through main() tests
    raise SystemExit(main())
