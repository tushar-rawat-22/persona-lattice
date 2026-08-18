# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from .convergence import ConvergedResearchReport, ResearchNode
from .correlation import (
    CorrelationEngine,
    CorrelationFactorInput,
    CorrelationRequest,
    FactorKind,
)
from .evidence import (
    EvidenceStore,
    IdentifierKind,
    ObservationSourceKind,
    create_database_engine,
    create_schema,
    make_session_factory,
    normalize_identifier,
)
from .evidence.database import session_scope
from .research import QuickObservation, ResearchKind


@dataclass(frozen=True, slots=True)
class _Candidate:
    node: ResearchNode
    observation_index: int
    quick: QuickObservation
    stored_observation_id: Any
    source_kind: ObservationSourceKind


def _source_kind(source: str) -> ObservationSourceKind:
    if source == "sherlock":
        return ObservationSourceKind.PROVIDER
    if source.endswith("_public_api"):
        return ObservationSourceKind.PUBLIC_PROFILE
    if source == "brave_public_web_index":
        return ObservationSourceKind.PUBLIC_WEB
    if source in {"public_dns_infrastructure", "libphonenumber_metadata", "local_normalization"}:
        return ObservationSourceKind.REGISTRY
    return ObservationSourceKind.PUBLIC_WEB


def _result_payload(result, *, candidate: _Candidate) -> dict[str, object]:
    return {
        "candidate_node": candidate.node.key,
        "candidate_observation_index": candidate.observation_index,
        "outcome": result.outcome.value,
        "evidence_score": result.evidence_score,
        "calibration_status": result.calibration_status.value,
        "positive_independence_groups": result.positive_independence_groups,
        "is_identity_claim": result.is_identity_claim,
        "policy_version": result.policy_version,
        "input_digest": result.input_digest,
        "output_digest": result.output_digest,
        "factors": [
            {
                "kind": factor.kind.value,
                "independence_group": factor.independence_group,
                "base_weight": factor.base_weight,
                "applied_weight": factor.applied_weight,
                "status": factor.status.value,
                "rationale": factor.rationale,
                "veto": factor.veto,
            }
            for factor in result.factors
        ],
    }


def evaluate_live_m5(report: ConvergedResearchReport) -> dict[str, object]:
    """Admit a converged run into an ephemeral M1-M5 graph and evaluate candidates.

    The evidence graph exists only in memory for this evaluation. The retained case
    stores the resulting deterministic M5 decision records, so deleting the case
    does not leave a second hidden copy of personal research data in another DB.
    """

    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    create_schema(engine)
    factory = make_session_factory(engine)
    evaluated_at = datetime.now(UTC)

    with session_scope(factory) as session:
        store = EvidenceStore(session)
        subject = store.add_subject()
        identifier_by_node: dict[str, Any] = {}
        seed_identifier = None

        for node in report.nodes:
            kind = IdentifierKind(node.kind.value)
            normalized = normalize_identifier(kind, node.report.normalized_value)
            identifier = store.add_identifier(subject.id, normalized)
            identifier_by_node[node.key] = identifier
            if node.depth == 0:
                seed_identifier = identifier

        candidates: list[_Candidate] = []
        observation_count = 0
        for node in report.nodes:
            identifier = identifier_by_node[node.key]
            for observation_index, quick in enumerate(node.report.observations):
                payload = dict(quick.details)
                payload.update(
                    {
                        "summary": quick.summary,
                        "research_node_key": node.key,
                        "pivot_reason": node.pivot_reason.value,
                    }
                )
                source_kind = _source_kind(quick.source)
                stored = store.add_observation(
                    subject_id=subject.id,
                    identifier_id=identifier.id,
                    source_kind=source_kind,
                    source_name=quick.source,
                    source_locator=quick.source_locator,
                    payload=payload,
                    retrieved_at=evaluated_at,
                )
                observation_count += 1
                if (
                    node.kind is ResearchKind.USERNAME
                    and payload.get("account_candidate") is True
                    and payload.get("identity_claim") is False
                ):
                    candidates.append(
                        _Candidate(
                            node=node,
                            observation_index=observation_index,
                            quick=quick,
                            stored_observation_id=stored.id,
                            source_kind=source_kind,
                        )
                    )

        correlation_engine = CorrelationEngine(session)
        evaluations: list[dict[str, object]] = []
        for candidate in candidates:
            factors = [
                CorrelationFactorInput(
                    kind=FactorKind.SAME_USERNAME,
                    observation_ids=(candidate.stored_observation_id,),
                    rationale="Public account candidate uses the researched username.",
                )
            ]

            # Exact identifier overlap is only promoted when the *original operator
            # seed* was an email and that exact email is explicitly public on the
            # candidate. Emails discovered from the candidate itself are not allowed
            # to bootstrap their own strong factor.
            if seed_identifier is not None and seed_identifier.kind is IdentifierKind.EMAIL:
                public_email = candidate.quick.details.get("email") or candidate.quick.details.get(
                    "public_email"
                )
                if (
                    isinstance(public_email, str)
                    and public_email.casefold() == seed_identifier.normalized_value.casefold()
                ):
                    support = store.add_observation(
                        subject_id=subject.id,
                        identifier_id=seed_identifier.id,
                        source_kind=candidate.source_kind,
                        source_name=candidate.quick.source,
                        source_locator=candidate.quick.source_locator,
                        payload={
                            "candidate_observation_id": str(candidate.stored_observation_id),
                            "confirmed_identifier_ids": [str(seed_identifier.id)],
                            "evidence_type": "exact_public_seed_email_overlap",
                            "identity_claim": False,
                        },
                        retrieved_at=evaluated_at,
                    )
                    observation_count += 1
                    factors.append(
                        CorrelationFactorInput(
                            kind=FactorKind.EXACT_CONFIRMED_IDENTIFIER_OVERLAP,
                            observation_ids=(support.id,),
                            identifier_ids=(seed_identifier.id,),
                            rationale=(
                                "The original email seed is explicitly public on this account candidate."
                            ),
                        )
                    )

            result = correlation_engine.correlate(
                CorrelationRequest(
                    subject_id=subject.id,
                    candidate_observation_id=candidate.stored_observation_id,
                    evaluated_at=evaluated_at,
                    factors=tuple(factors),
                )
            )
            evaluations.append(_result_payload(result, candidate=candidate))

        return {
            "engine": "m5-deterministic-evidence-strength",
            "subject_id": str(subject.id),
            "evaluated_at": evaluated_at.isoformat(),
            "identifier_count": len(identifier_by_node),
            "observation_count": observation_count,
            "candidate_count": len(candidates),
            "evaluations": evaluations,
            "calibration_status": "uncalibrated",
            "is_identity_claim": False,
            "interpretation": (
                "Live provider evidence was admitted to an ephemeral canonical evidence graph and "
                "evaluated under M5. Scores are evidence-strength triage, never identity probability."
            ),
        }
