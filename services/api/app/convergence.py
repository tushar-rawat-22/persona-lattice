# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from collections import Counter, deque
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import StrEnum

from .converged_report import validate_converged_provenance_references
from .intelligence import (
    FrontierDecision,
    LeadFrontier,
    LeadKind,
    compatibility_frontier_limits,
    extract_observation_leads,
)
from .intelligence.contracts import LeadCandidate, canonicalize_lead
from .intelligence.source_reporting import build_source_run_report
from .models import Purpose
from .research import QuickResearchReport, ResearchKind, run_quick_research


MAX_CONVERGENCE_DEPTH = 2
MAX_CONVERGENCE_NODES = 12
_LEAD_POLICY_VERSION = "v2-evidence-lead-policy-v1"
_BUDGET_STOP_DECISIONS = frozenset(
    {
        FrontierDecision.DEPTH_LIMIT,
        FrontierDecision.NODE_LIMIT,
        FrontierDecision.EDGE_LIMIT,
        FrontierDecision.KIND_LIMIT,
        FrontierDecision.PARENT_FANOUT_LIMIT,
    }
)


class PivotReason(StrEnum):
    SEED = "seed"
    PUBLIC_EMAIL = "public_email"
    PUBLIC_USERNAME = "public_username"
    PUBLIC_URL = "public_url"


@dataclass(frozen=True, slots=True)
class ResearchNode:
    kind: ResearchKind
    value: str
    depth: int
    parent_key: str | None
    pivot_reason: PivotReason
    report: QuickResearchReport

    @property
    def key(self) -> str:
        lead_kind = LeadKind(self.kind.value)
        _display_value, comparison_key = canonicalize_lead(
            lead_kind,
            self.report.normalized_value,
        )
        return f"{lead_kind.value}:{comparison_key}"


@dataclass(frozen=True, slots=True)
class ResearchEdge:
    parent_key: str
    child_key: str
    reason: PivotReason
    source: str
    source_locator: str
    lead_decision_index: int


@dataclass(frozen=True, slots=True)
class LeadTraversalRecord:
    parent_key: str
    parent_depth: int
    candidate: LeadCandidate
    decision: FrontierDecision
    source_observation_index: int
    child_key: str | None = None


@dataclass(frozen=True, slots=True)
class ConvergedResearchReport:
    seed_kind: ResearchKind
    seed_value: str
    nodes: tuple[ResearchNode, ...]
    edges: tuple[ResearchEdge, ...]
    warnings: tuple[str, ...]
    truncated: bool
    lead_decisions: tuple[LeadTraversalRecord, ...] = ()
    blocked_field_names: tuple[str, ...] = ()


ResearchRunner = Callable[..., Awaitable[QuickResearchReport]]


def _lead_candidates(
    report: QuickResearchReport,
) -> tuple[tuple[tuple[LeadCandidate, int], ...], tuple[str, ...]]:
    """Extract reviewed lead candidates while preserving distinct provenance origins."""

    candidates: dict[tuple[str, str, str, str], tuple[LeadCandidate, int]] = {}
    blocked_fields: set[str] = set()

    for observation_index, observation in enumerate(report.observations):
        extraction = extract_observation_leads(
            details=observation.details,
            source=observation.source,
            source_locator=observation.source_locator,
        )
        blocked_fields.update(extraction.blocked_field_names)
        for candidate in extraction.candidates:
            origin_key = (
                candidate.key,
                candidate.source,
                candidate.source_locator,
                candidate.field_name,
            )
            candidates.setdefault(origin_key, (candidate, observation_index))

    ordered = tuple(
        sorted(
            candidates.values(),
            key=lambda item: (
                item[0].kind.value,
                item[0].comparison_key,
                item[0].source,
                item[0].source_locator,
                item[0].field_name,
                item[1],
            ),
        )
    )
    return ordered, tuple(sorted(blocked_fields))


def _pivot_reason(candidate: LeadCandidate) -> PivotReason:
    try:
        return PivotReason(candidate.reason.value)
    except ValueError as exc:  # defensive: auto-pivot rules must map to a public pivot reason
        raise RuntimeError(
            f"Automatic lead reason {candidate.reason.value!r} is not a convergence pivot."
        ) from exc


def _node_source_run_report(report: QuickResearchReport) -> dict[str, object]:
    """Project the canonical typed source-run contract without compatibility inference."""

    return build_source_run_report(report.source_runs)


def _node_payload(node: ResearchNode) -> dict[str, object]:
    return {
        "key": node.key,
        "kind": node.kind.value,
        "normalized_value": node.report.normalized_value,
        "depth": node.depth,
        "parent_key": node.parent_key,
        "pivot_reason": node.pivot_reason.value,
        "warnings": list(node.report.warnings),
        "source_runs": _node_source_run_report(node.report),
        "observations": [
            {
                "source": observation.source,
                "source_locator": observation.source_locator,
                "summary": observation.summary,
                "details": dict(observation.details),
            }
            for observation in node.report.observations
        ],
    }


def _lead_decision_payload(
    record: LeadTraversalRecord,
    nodes_by_key: dict[str, ResearchNode],
) -> dict[str, object]:
    candidate = record.candidate
    parent = nodes_by_key.get(record.parent_key)
    if parent is None:
        raise ValueError("Lead decision parent_key must reference a retained research node.")
    if not 0 <= record.source_observation_index < len(parent.report.observations):
        raise ValueError("Lead decision source_observation_index is out of range.")
    observation = parent.report.observations[record.source_observation_index]
    if observation.source != candidate.source or observation.source_locator != candidate.source_locator:
        raise ValueError("Lead decision provenance does not match its canonical parent observation.")
    if candidate.field_name not in observation.details:
        raise ValueError("Lead decision source_field is absent from its canonical parent observation.")
    return {
        "parent_key": record.parent_key,
        "parent_depth": record.parent_depth,
        "lead_key": candidate.key,
        "kind": candidate.kind.value,
        "normalized_value": candidate.value,
        "reason": candidate.reason.value,
        "disposition": candidate.disposition.value,
        "decision": record.decision.value,
        "source_observation_index": record.source_observation_index,
        "source_field": candidate.field_name,
        "child_key": record.child_key,
    }


def _edge_payload(
    edge: ResearchEdge,
    lead_decisions: tuple[LeadTraversalRecord, ...],
) -> dict[str, object]:
    if not 0 <= edge.lead_decision_index < len(lead_decisions):
        raise ValueError("Edge lead_decision_index is out of range.")
    record = lead_decisions[edge.lead_decision_index]
    if record.decision is not FrontierDecision.ADMITTED:
        raise ValueError("Edge must reference an admitted lead decision.")
    if record.parent_key != edge.parent_key or record.child_key != edge.child_key:
        raise ValueError("Edge structure does not match its admitted lead decision.")
    if _pivot_reason(record.candidate) is not edge.reason:
        raise ValueError("Edge reason does not match its admitted lead decision.")
    if record.candidate.source != edge.source or record.candidate.source_locator != edge.source_locator:
        raise ValueError("Edge provenance does not match its admitted lead decision.")
    return {
        "parent_key": edge.parent_key,
        "child_key": edge.child_key,
        "reason": edge.reason.value,
        "lead_decision_index": edge.lead_decision_index,
    }


def build_converged_payload(report: ConvergedResearchReport) -> dict[str, object]:
    source_names = sorted(
        {
            observation.source
            for node in report.nodes
            for observation in node.report.observations
        }
    )
    nodes_by_key = {node.key: node for node in report.nodes}
    if len(nodes_by_key) != len(report.nodes):
        raise ValueError("Converged report contains duplicate research node keys.")
    decision_counts = Counter(record.decision.value for record in report.lead_decisions)
    payload: dict[str, object] = {
        "report_version": "private-converged-evidence-report-v1",
        "seed": {
            "kind": report.seed_kind.value,
            "normalized_value": report.seed_value,
        },
        "executive_summary": {
            "research_node_count": len(report.nodes),
            "pivot_edge_count": len(report.edges),
            "lead_decision_count": len(report.lead_decisions),
            "source_count": len(source_names),
            "sources": source_names,
            "identity_probability": None,
            "identity_claim": False,
            "truncated": report.truncated,
            "interpretation": (
                "Public-evidence convergence only. Discovered identifiers are research leads, "
                "not proof that they belong to the same person."
            ),
        },
        "nodes": [_node_payload(node) for node in report.nodes],
        "edges": [_edge_payload(edge, report.lead_decisions) for edge in report.edges],
        "lead_graph": {
            "policy_version": _LEAD_POLICY_VERSION,
            "decision_counts": dict(sorted(decision_counts.items())),
            "decisions": [
                _lead_decision_payload(record, nodes_by_key) for record in report.lead_decisions
            ],
            "blocked_field_names": list(report.blocked_field_names),
        },
        "warnings": list(report.warnings),
        "safety_boundary": {
            "max_depth": MAX_CONVERGENCE_DEPTH,
            "max_nodes": MAX_CONVERGENCE_NODES,
            "private_account_bypass": False,
            "covert_ip_discovery": False,
            "identity_claim": False,
        },
        "provenance_rule": (
            "Canonical node observations own provider source locators. Lead decisions reference "
            "their source observation, and admitted edges reference the corresponding decision."
        ),
    }
    validate_converged_provenance_references(payload)

    # Local import intentionally avoids coupling the research graph construction to
    # the correlation module at import time. M5 receives an ephemeral canonical
    # evidence graph, so case deletion remains the only retained-data deletion path.
    from .live_m5 import evaluate_live_m5

    payload["m5"] = evaluate_live_m5(report)
    return payload


async def run_converged_research(
    *,
    kind: ResearchKind,
    value: str,
    purpose: Purpose,
    consent_acknowledged: bool,
    runner: ResearchRunner = run_quick_research,
    max_depth: int = MAX_CONVERGENCE_DEPTH,
    max_nodes: int = MAX_CONVERGENCE_NODES,
) -> ConvergedResearchReport:
    if not 0 <= max_depth <= MAX_CONVERGENCE_DEPTH:
        raise ValueError(f"max_depth must be between 0 and {MAX_CONVERGENCE_DEPTH}.")
    if not 1 <= max_nodes <= MAX_CONVERGENCE_NODES:
        raise ValueError(f"max_nodes must be between 1 and {MAX_CONVERGENCE_NODES}.")

    seed_report = await runner(
        kind=kind,
        value=value,
        purpose=purpose,
        consent_acknowledged=consent_acknowledged,
    )
    seed_node = ResearchNode(
        kind=kind,
        value=value,
        depth=0,
        parent_key=None,
        pivot_reason=PivotReason.SEED,
        report=seed_report,
    )

    frontier = LeadFrontier(
        seed_key=seed_node.key,
        seed_kind=LeadKind(kind.value),
        limits=compatibility_frontier_limits(max_depth=max_depth, max_nodes=max_nodes),
    )
    nodes: list[ResearchNode] = [seed_node]
    edges: list[ResearchEdge] = []
    lead_decisions: list[LeadTraversalRecord] = []
    blocked_fields: set[str] = set()
    warnings: list[str] = list(seed_report.warnings)
    queue: deque[ResearchNode] = deque([seed_node])
    truncated = False

    while queue:
        parent = queue.popleft()
        candidates, parent_blocked_fields = _lead_candidates(parent.report)
        blocked_fields.update(parent_blocked_fields)
        for field_name in parent_blocked_fields:
            warnings.append(
                f"Blocked lead field {field_name!r} was not admitted to recursive research."
            )

        for lead, source_observation_index in candidates:
            evaluation = frontier.consider(
                lead,
                parent_key=parent.key,
                parent_depth=parent.depth,
            )
            if evaluation.decision is not FrontierDecision.ENQUEUE:
                lead_decisions.append(
                    LeadTraversalRecord(
                        parent_key=parent.key,
                        parent_depth=parent.depth,
                        candidate=lead,
                        decision=evaluation.decision,
                        source_observation_index=source_observation_index,
                    )
                )
                if evaluation.decision in _BUDGET_STOP_DECISIONS:
                    truncated = True
                continue

            pivot_kind = ResearchKind(lead.kind.value)
            try:
                pivot_report = await runner(
                    kind=pivot_kind,
                    value=lead.value,
                    purpose=purpose,
                    consent_acknowledged=consent_acknowledged,
                )
            except Exception as exc:  # provider failures are isolated per public pivot
                failure_decision = frontier.fail(lead)
                lead_decisions.append(
                    LeadTraversalRecord(
                        parent_key=parent.key,
                        parent_depth=parent.depth,
                        candidate=lead,
                        decision=failure_decision,
                        source_observation_index=source_observation_index,
                    )
                )
                warnings.append(
                    f"Pivot {pivot_kind.value} from {lead.source} could not be researched: "
                    f"{type(exc).__name__}."
                )
                continue

            candidate = ResearchNode(
                kind=pivot_kind,
                value=lead.value,
                depth=parent.depth + 1,
                parent_key=parent.key,
                pivot_reason=_pivot_reason(lead),
                report=pivot_report,
            )
            admission = frontier.admit(
                lead,
                actual_key=candidate.key,
                parent_key=parent.key,
            )
            lead_decisions.append(
                LeadTraversalRecord(
                    parent_key=parent.key,
                    parent_depth=parent.depth,
                    candidate=lead,
                    decision=admission,
                    source_observation_index=source_observation_index,
                    child_key=candidate.key,
                )
            )
            lead_decision_index = len(lead_decisions) - 1
            if admission is not FrontierDecision.ADMITTED:
                if admission in _BUDGET_STOP_DECISIONS:
                    truncated = True
                continue

            nodes.append(candidate)
            edges.append(
                ResearchEdge(
                    parent_key=parent.key,
                    child_key=candidate.key,
                    reason=_pivot_reason(lead),
                    source=lead.source,
                    source_locator=lead.source_locator,
                    lead_decision_index=lead_decision_index,
                )
            )
            warnings.extend(pivot_report.warnings)
            queue.append(candidate)

    return ConvergedResearchReport(
        seed_kind=kind,
        seed_value=seed_report.normalized_value,
        nodes=tuple(nodes),
        edges=tuple(edges),
        warnings=tuple(dict.fromkeys(warnings)),
        truncated=truncated,
        lead_decisions=tuple(lead_decisions),
        blocked_field_names=tuple(sorted(blocked_fields)),
    )
