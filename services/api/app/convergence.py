# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from collections import deque
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import StrEnum

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
        return f"{self.kind.value}:{self.report.normalized_value.casefold()}"


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


def _text(value: object) -> str | None:
    if value is None or isinstance(value, bool):
        return None
    text = str(value).strip()
    return text or None


def _pivot_candidates(report: QuickResearchReport) -> list[tuple[ResearchKind, str, PivotReason, str, str]]:
    """Return only reviewed attributable public fields that may become research seeds.

    The aliases below match the allowlisted public fields returned by the existing
    GitHub, GitLab and Codeforces integrations. Location, company, subscriber
    metadata, Discord/LinkedIn identifiers and network identifiers remain display
    evidence only; they are not autonomous pivots.
    """

    candidates: list[tuple[ResearchKind, str, PivotReason, str, str]] = []
    for observation in report.observations:
        details = observation.details
        fields = (
            (ResearchKind.EMAIL, details.get("email"), PivotReason.PUBLIC_EMAIL),
            (ResearchKind.EMAIL, details.get("public_email"), PivotReason.PUBLIC_EMAIL),
            (ResearchKind.USERNAME, details.get("username"), PivotReason.PUBLIC_USERNAME),
            (ResearchKind.USERNAME, details.get("login"), PivotReason.PUBLIC_USERNAME),
            (ResearchKind.USERNAME, details.get("handle"), PivotReason.PUBLIC_USERNAME),
            (ResearchKind.USERNAME, details.get("twitter_username"), PivotReason.PUBLIC_USERNAME),
            (ResearchKind.USERNAME, details.get("twitter"), PivotReason.PUBLIC_USERNAME),
            (ResearchKind.URL, details.get("blog"), PivotReason.PUBLIC_URL),
            (ResearchKind.URL, details.get("website_url"), PivotReason.PUBLIC_URL),
        )
        for kind, raw, reason in fields:
            value = _text(raw)
            if value is None:
                continue
            candidates.append(
                (kind, value, reason, observation.source, observation.source_locator)
            )
    return candidates


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
    attempted_raw = {(kind.value, value.strip().casefold())}
    queue: deque[ResearchNode] = deque([seed_node])
    truncated = False

    while queue:
        parent = queue.popleft()
        if parent.depth >= max_depth:
            continue

        for pivot_kind, pivot_value, reason, source, source_locator in _pivot_candidates(
            parent.report
        ):
            if len(nodes) >= max_nodes:
                truncated = True
                queue.clear()
                break

            raw_key = (pivot_kind.value, pivot_value.strip().casefold())
            if raw_key in attempted_raw:
                continue
            attempted_raw.add(raw_key)

            try:
                pivot_report = await runner(
                    kind=pivot_kind,
                    value=pivot_value,
                    purpose=purpose,
                    consent_acknowledged=consent_acknowledged,
                )
            except Exception as exc:  # provider failures are isolated per public pivot
                warnings.append(
                    f"Pivot {pivot_kind.value} from {source} could not be researched: {type(exc).__name__}."
                )
                continue

            candidate = ResearchNode(
                kind=pivot_kind,
                value=pivot_value,
                depth=parent.depth + 1,
                parent_key=parent.key,
                pivot_reason=reason,
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
                    reason=reason,
                    source=source,
                    source_locator=source_locator,
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
