# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CaseEvidenceSynopsis:
    mode: str
    available: bool
    observation_count: int | None
    source_count: int | None
    sources: tuple[str, ...]
    warning_count: int | None
    contradiction_count: int | None
    source_state_counts: dict[str, int]
    coverage_gap_count: int | None
    truncated: bool | None
    m5_present: bool


def _mapping(value: object) -> Mapping[str, object] | None:
    return value if isinstance(value, Mapping) else None


def _sequence(value: object) -> Sequence[object] | None:
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(value, Sequence):
        return None
    return value


def _string_tuple(value: object) -> tuple[str, ...]:
    items = _sequence(value)
    if items is None:
        return ()
    return tuple(item for item in items if isinstance(item, str) and item)


def _int_value(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


def _count_sequence(value: object) -> int | None:
    items = _sequence(value)
    return len(items) if items is not None else None


def _state_counts(value: object) -> dict[str, int]:
    payload = _mapping(value)
    if payload is None:
        return {}
    counts: dict[str, int] = {}
    for key, count in payload.items():
        if isinstance(key, str) and key and (parsed := _int_value(count)) is not None:
            counts[key] = parsed
    return dict(sorted(counts.items()))


def _quick_synopsis(report: Mapping[str, object]) -> CaseEvidenceSynopsis | None:
    structured = _mapping(report.get("structured_report"))
    source_runs = _mapping(report.get("source_runs"))
    if structured is None or source_runs is None:
        return None
    executive = _mapping(structured.get("executive_summary"))
    if executive is None:
        return None

    observation_count = _int_value(executive.get("observation_count"))
    source_count = _int_value(executive.get("source_count"))
    sources = _string_tuple(executive.get("sources"))
    warnings = _sequence(report.get("warnings"))
    contradictions = _sequence(structured.get("contradiction_observation_indexes"))
    coverage_gaps = _sequence(structured.get("coverage_gaps"))
    if observation_count is None or source_count is None or warnings is None:
        return None

    return CaseEvidenceSynopsis(
        mode="quick",
        available=True,
        observation_count=observation_count,
        source_count=source_count,
        sources=sources,
        warning_count=len(warnings),
        contradiction_count=len(contradictions) if contradictions is not None else None,
        source_state_counts=_state_counts(source_runs.get("state_counts")),
        coverage_gap_count=len(coverage_gaps) if coverage_gaps is not None else None,
        truncated=False,
        m5_present=False,
    )


def _converged_synopsis(report: Mapping[str, object]) -> CaseEvidenceSynopsis | None:
    converged = _mapping(report.get("converged_report"))
    if converged is None:
        return None
    executive = _mapping(converged.get("executive_summary"))
    nodes = _sequence(converged.get("nodes"))
    warnings = _sequence(converged.get("warnings"))
    lead_graph = _mapping(converged.get("lead_graph"))
    if executive is None or nodes is None or warnings is None or lead_graph is None:
        return None

    source_count = _int_value(executive.get("source_count"))
    sources = _string_tuple(executive.get("sources"))
    if source_count is None:
        return None

    observation_count = 0
    contradiction_count = 0
    state_counts: Counter[str] = Counter()
    for node_value in nodes:
        node = _mapping(node_value)
        if node is None:
            return None
        observations = _sequence(node.get("observations"))
        source_runs = _mapping(node.get("source_runs"))
        if observations is None or source_runs is None:
            return None
        observation_count += len(observations)
        state_counts.update(_state_counts(source_runs.get("state_counts")))
        for observation_value in observations:
            observation = _mapping(observation_value)
            details = _mapping(observation.get("details")) if observation is not None else None
            if details is not None and (
                details.get("contradiction") is True or details.get("account_state") == "illegal"
            ):
                contradiction_count += 1

    blocked_fields = _sequence(lead_graph.get("blocked_field_names"))
    truncated = executive.get("truncated")
    if not isinstance(truncated, bool):
        return None

    return CaseEvidenceSynopsis(
        mode="converged",
        available=True,
        observation_count=observation_count,
        source_count=source_count,
        sources=sources,
        warning_count=len(warnings),
        contradiction_count=contradiction_count,
        source_state_counts=dict(sorted(state_counts.items())),
        coverage_gap_count=len(blocked_fields) if blocked_fields is not None else None,
        truncated=truncated,
        m5_present=isinstance(converged.get("m5"), Mapping),
    )


def build_case_evidence_synopsis(report: Mapping[str, object]) -> CaseEvidenceSynopsis:
    """Project one retained report into privacy-bounded operator decision metadata.

    The synopsis deliberately excludes observation details, source locators, identifier values,
    provider payloads and M5 scores. Unsupported legacy shapes remain explicit instead of
    fabricating zero-count evidence.
    """

    synopsis = _quick_synopsis(report) or _converged_synopsis(report)
    if synopsis is not None:
        return synopsis
    return CaseEvidenceSynopsis(
        mode="legacy_or_unknown",
        available=False,
        observation_count=None,
        source_count=None,
        sources=(),
        warning_count=None,
        contradiction_count=None,
        source_state_counts={},
        coverage_gap_count=None,
        truncated=None,
        m5_present=False,
    )
