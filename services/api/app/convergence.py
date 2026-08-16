# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from collections import deque
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import StrEnum

from .intelligence import LeadDisposition, LeadKind, extract_observation_leads
from .intelligence.contracts import LeadCandidate, canonicalize_lead
from .models import Purpose
from .research import QuickResearchReport, ResearchKind, run_quick_research


MAX_CONVERGENCE_DEPTH = 2
MAX_CONVERGENCE_NODES = 12


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


@dataclass(frozen=True, slots=True)
class ConvergedResearchReport:
    seed_kind: ResearchKind
    seed_value: str
    nodes: tuple[ResearchNode, ...]
    edges: tuple[ResearchEdge, ...]
    warnings: tuple[str, ...]
    truncated: bool


ResearchRunner = Callable[..., Awaitable[QuickResearchReport]]


def _pivot_candidates(
    report: QuickResearchReport,
) -> tuple[tuple[LeadCandidate, ...], tuple[str, ...]]:
    """Extract only policy-approved automatic pivots from reviewed observations.

    The intelligence extractor also models review-only/display-only leads. Those
    remain available to future UI/report layers but are deliberately not executed
    by the current convergence loop.
    """

    candidates: dict[str, LeadCandidate] = {}
    blocked_fields: set[str] = set()

    for observation in report.observations:
        extraction = extract_observation_leads(
            details=observation.details,
            source=observation.source,
            source_locator=observation.source_locator,
        )
        blocked_fields.update(extraction.blocked_field_names)
        for candidate in extraction.candidates:
            if candidate.disposition is not LeadDisposition.AUTO_PIVOT:
                continue
            candidates.setdefault(candidate.key, candidate)

    ordered = tuple(
        sorted(
            candidates.values(),
            key=lambda item: (item.kind.value, item.comparison_key, item.source, item.field_name),
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


def _node_payload(node: ResearchNode) -> dict[str, object]:
    return {
        "key": node.key,
        "kind": node.kind.value,
        "normalized_value": node.report.normalized_value,
        "depth": node.depth,
        "parent_key": node.parent_key,
        "pivot_reason": node.pivot_reason.value,
        "warnings": list(node.report.warnings),
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


def build_converged_payload(report: ConvergedResearchReport) -> dict[str, object]:
    source_names = sorted(
        {
            observation.source
            for node in report.nodes
            for observation in node.report.observations
        }
    )
    payload: dict[str, object] = {
        "report_version": "private-converged-evidence-report-v1",
        "seed": {
            "kind": report.seed_kind.value,
            "normalized_value": report.seed_value,
        },
        "executive_summary": {
            "research_node_count": len(report.nodes),
            "pivot_edge_count": len(report.edges),
            "source_count": len(source_names),
            "sources": source_names,
            "identity_probability": None,
            "identity_claim": False,
            "truncated": report.truncated,
            "interpretation": (
                "Public-evidence convergence only. Discovered identifiers are research pivots, "
                "not proof that they belong to the same person."
            ),
        },
        "nodes": [_node_payload(node) for node in report.nodes],
        "edges": [
            {
                "parent_key": edge.parent_key,
                "child_key": edge.child_key,
                "reason": edge.reason.value,
                "source": edge.source,
                "source_locator": edge.source_locator,
            }
            for edge in report.edges
        ],
        "warnings": list(report.warnings),
        "safety_boundary": {
            "max_depth": MAX_CONVERGENCE_DEPTH,
            "max_nodes": MAX_CONVERGENCE_NODES,
            "private_account_bypass": False,
            "covert_ip_discovery": False,
            "identity_claim": False,
        },
        "provenance_rule": (
            "Every pivot must originate from an allowlisted public field and retain its source locator."
        ),
    }

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

    nodes: list[ResearchNode] = [seed_node]
    edges: list[ResearchEdge] = []
    warnings: list[str] = list(seed_report.warnings)
    visited = {seed_node.key}
    attempted = {seed_node.key}
    queue: deque[ResearchNode] = deque([seed_node])
    truncated = False

    while queue:
        parent = queue.popleft()
        if parent.depth >= max_depth:
            continue

        pivot_candidates, blocked_fields = _pivot_candidates(parent.report)
        for field_name in blocked_fields:
            warnings.append(
                f"Blocked lead field {field_name!r} was not admitted to recursive research."
            )

        for lead in pivot_candidates:
            if len(nodes) >= max_nodes:
                truncated = True
                queue.clear()
                break

            if lead.key in attempted:
                continue
            attempted.add(lead.key)

            pivot_kind = ResearchKind(lead.kind.value)
            try:
                pivot_report = await runner(
                    kind=pivot_kind,
                    value=lead.value,
                    purpose=purpose,
                    consent_acknowledged=consent_acknowledged,
                )
            except Exception as exc:  # provider failures are isolated per public pivot
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
            if candidate.key in visited:
                continue

            visited.add(candidate.key)
            nodes.append(candidate)
            edges.append(
                ResearchEdge(
                    parent_key=parent.key,
                    child_key=candidate.key,
                    reason=_pivot_reason(lead),
                    source=lead.source,
                    source_locator=lead.source_locator,
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
    )
