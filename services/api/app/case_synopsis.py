# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Mapping
import json
import sys
from uuid import UUID

from .cases import CASE_STORE, StoredCase


_SYNOPSIS_VERSION = "analyst-case-synopsis-v1"
_METHOD_LIMITS = (
    "Evidence synopsis only; PersonaLattice does not assert identity without corroborating evidence.",
    "Same-handle overlap is a research lead, not proof that accounts are controlled by the same person.",
    "M5 outputs, when present, are uncalibrated and non-probabilistic; they are not identity probabilities.",
)


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, dict) else {}


def _mappings(value: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, dict))


def _strings(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _count_map(value: object) -> Counter[str]:
    counts: Counter[str] = Counter()
    if not isinstance(value, dict):
        return counts
    for key, count in value.items():
        if isinstance(key, str) and isinstance(count, int) and not isinstance(count, bool) and count >= 0:
            counts[key] += count
    return counts


def _is_contradiction(observation: Mapping[str, object]) -> bool:
    details = _mapping(observation.get("details"))
    return details.get("contradiction") is True or details.get("account_state") == "illegal"


def _quick_synopsis(report: Mapping[str, object]) -> dict[str, object]:
    observations = _mappings(report.get("observations"))
    structured = _mapping(report.get("structured_report"))
    executive = _mapping(structured.get("executive_summary"))
    source_runs = _mapping(report.get("source_runs"))

    indexed_contradictions = {
        item
        for item in structured.get("contradiction_observation_indexes", [])
        if isinstance(item, int) and not isinstance(item, bool) and 0 <= item < len(observations)
    } if isinstance(structured.get("contradiction_observation_indexes"), list) else set()
    indexed_contradictions.update(
        index for index, observation in enumerate(observations) if _is_contradiction(observation)
    )
    sources = sorted(
        {
            source
            for observation in observations
            if isinstance((source := observation.get("source")), str) and source
        }
    )
    warnings = _strings(report.get("warnings"))
    coverage_gaps = _strings(structured.get("coverage_gaps"))

    return {
        "workflow": {"mode": "quick", "truncated": False},
        "evidence_summary": {
            "observation_count": len(observations),
            "source_count": len(sources),
            "sources": sources,
            "connected_identifier_count": executive.get("connected_identifier_count", 0),
            "public_account_candidate_count": executive.get("public_account_candidate_count", 0),
            "contradiction_count": len(indexed_contradictions),
            "warning_count": len(warnings),
            "coverage_gap_count": len(coverage_gaps),
            "identity_probability": None,
            "identity_claim": False,
        },
        "source_states": {
            "record_count": source_runs.get("record_count", 0),
            "state_counts": dict(sorted(_count_map(source_runs.get("state_counts")).items())),
            "reason_counts": dict(sorted(_count_map(source_runs.get("reason_counts")).items())),
            "evaluation": dict(_mapping(source_runs.get("evaluation"))),
        },
        "contradiction_observation_indexes": sorted(indexed_contradictions),
        "warnings": warnings,
        "coverage_gaps": coverage_gaps,
    }


def _converged_synopsis(report: Mapping[str, object]) -> dict[str, object]:
    converged = _mapping(report.get("converged_report"))
    executive = _mapping(converged.get("executive_summary"))
    nodes = _mappings(converged.get("nodes"))
    source_names: set[str] = set()
    contradiction_refs: list[dict[str, object]] = []
    state_counts: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()
    source_record_count = 0
    observation_count = 0

    for node_index, node in enumerate(nodes):
        observations = _mappings(node.get("observations"))
        observation_count += len(observations)
        for observation_index, observation in enumerate(observations):
            source = observation.get("source")
            if isinstance(source, str) and source:
                source_names.add(source)
            if _is_contradiction(observation):
                contradiction_refs.append(
                    {"node_index": node_index, "observation_index": observation_index}
                )
        source_runs = _mapping(node.get("source_runs"))
        record_count = source_runs.get("record_count", 0)
        if isinstance(record_count, int) and not isinstance(record_count, bool) and record_count >= 0:
            source_record_count += record_count
        state_counts.update(_count_map(source_runs.get("state_counts")))
        reason_counts.update(_count_map(source_runs.get("reason_counts")))

    warnings = _strings(converged.get("warnings"))
    lead_graph = _mapping(converged.get("lead_graph"))

    return {
        "workflow": {
            "mode": "converged",
            "truncated": executive.get("truncated", False),
            "research_node_count": executive.get("research_node_count", len(nodes)),
            "pivot_edge_count": executive.get("pivot_edge_count", 0),
            "lead_decision_count": executive.get("lead_decision_count", 0),
            "lead_decision_counts": dict(_mapping(lead_graph.get("decision_counts"))),
        },
        "evidence_summary": {
            "observation_count": observation_count,
            "source_count": len(source_names),
            "sources": sorted(source_names),
            "contradiction_count": len(contradiction_refs),
            "warning_count": len(warnings),
            "coverage_gap_count": 0,
            "identity_probability": None,
            "identity_claim": False,
        },
        "source_states": {
            "record_count": source_record_count,
            "state_counts": dict(sorted(state_counts.items())),
            "reason_counts": dict(sorted(reason_counts.items())),
        },
        "contradiction_references": contradiction_refs,
        "warnings": warnings,
        "coverage_gaps": [],
    }


def build_case_synopsis(record: StoredCase) -> dict[str, object]:
    """Build a deterministic, read-only synopsis without duplicating retained lead values."""

    report = _mapping(record.report)
    content = (
        _converged_synopsis(report)
        if isinstance(report.get("converged_report"), dict)
        else _quick_synopsis(report)
    )
    return {
        "synopsis_version": _SYNOPSIS_VERSION,
        "case": {
            "id": str(record.id),
            "created_at": record.created_at.isoformat(),
            "expires_at": record.expires_at.isoformat(),
            "seed_kind": record.seed_kind.value,
        },
        **content,
        "method_limits": list(_METHOD_LIMITS),
        "provenance_rule": (
            "Contradiction references point back to canonical retained observations. Seed values, "
            "source locators and provider detail payloads are intentionally not duplicated here."
        ),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render a privacy-bounded synopsis for one retained PersonaLattice case."
    )
    parser.add_argument("case_id", type=UUID, help="retained case UUID")
    parser.add_argument("--pretty", action="store_true", help="pretty-print JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    record = CASE_STORE.get(args.case_id)
    if record is None:
        print("Case not found or expired.", file=sys.stderr)
        return 2
    payload = build_case_synopsis(record)
    if args.pretty:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
