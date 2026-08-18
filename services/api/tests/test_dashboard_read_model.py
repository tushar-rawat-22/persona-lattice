# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json

import pytest

from app.correlation import (
    CorrelationEngine,
    CorrelationFactorInput,
    CorrelationOutcome,
    CorrelationRequest,
    FactorKind,
    FactorStatus,
)
from app.correlation.models import CorrelationRun
from app.dashboard import (
    M6_READ_MODEL_VERSION,
    CaseReadModelService,
    DashboardReadModelError,
)
from app.evidence import (
    ClaimOrigin,
    EvidenceRelation,
    EvidenceStore,
    FreshnessState,
    IdentifierKind,
    ObservationSourceKind,
    create_database_engine,
    create_schema,
    make_session_factory,
    normalize_identifier,
)
from app.main import app

EVALUATED_AT = datetime(2026, 8, 16, 10, 0, tzinfo=timezone.utc)


@pytest.fixture
def synthetic_case():
    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    create_schema(engine)
    factory = make_session_factory(engine)
    with factory() as session:
        store = EvidenceStore(session)
        subject = store.add_subject("Synthetic M6 Subject")
        username = store.add_identifier(
            subject.id,
            normalize_identifier(IdentifierKind.USERNAME, "synthetic-m6"),
        )
        email = store.add_identifier(
            subject.id,
            normalize_identifier(IdentifierKind.EMAIL, "synthetic-m6@example.test"),
        )

        same_handle_candidate = store.add_observation(
            subject_id=subject.id,
            identifier_id=username.id,
            source_kind=ObservationSourceKind.PROVIDER,
            source_name="sherlock",
            source_locator="https://github.com/synthetic-m6",
            payload={
                "account_candidate": True,
                "identity_claim": False,
                "site": "GitHub",
                "profile_url": "https://github.com/synthetic-m6",
                "raw_secret": "must-not-enter-read-model",
            },
            retrieved_at=EVALUATED_AT - timedelta(hours=2),
            expires_at=EVALUATED_AT + timedelta(days=5),
        )
        contradicted_candidate = store.add_observation(
            subject_id=subject.id,
            identifier_id=username.id,
            source_kind=ObservationSourceKind.PROVIDER,
            source_name="sherlock",
            source_locator="https://www.reddit.com/user/synthetic-m6",
            payload={
                "account_candidate": True,
                "identity_claim": False,
                "site": "Reddit",
                "profile_url": "https://www.reddit.com/user/synthetic-m6",
            },
            retrieved_at=EVALUATED_AT - timedelta(hours=3),
            expires_at=EVALUATED_AT + timedelta(days=5),
        )
        email_proof = store.add_observation(
            subject_id=subject.id,
            source_kind=ObservationSourceKind.PUBLIC_WEB,
            source_name="synthetic-email-proof",
            source_locator="https://portfolio.example.test/contact",
            payload={
                "candidate_observation_id": str(contradicted_candidate.id),
                "confirmed_identifier_ids": [str(email.id)],
                "summary": "Synthetic portfolio repeats the confirmed email.",
            },
            retrieved_at=EVALUATED_AT - timedelta(days=1),
            expires_at=EVALUATED_AT + timedelta(days=5),
        )
        stale_cross_link = store.add_observation(
            subject_id=subject.id,
            source_kind=ObservationSourceKind.PUBLIC_WEB,
            source_name="synthetic-stale-cross-link",
            source_locator="https://archive.example.test/profile",
            payload={
                "candidate_observation_id": str(contradicted_candidate.id),
                "summary": "Expired synthetic cross-link.",
            },
            retrieved_at=EVALUATED_AT - timedelta(days=20),
            expires_at=EVALUATED_AT - timedelta(days=1),
        )
        contradiction = store.add_observation(
            subject_id=subject.id,
            source_kind=ObservationSourceKind.PUBLIC_WEB,
            source_name="synthetic-contradiction",
            source_locator="https://contradiction.example.test/fact",
            payload={
                "candidate_observation_id": str(contradicted_candidate.id),
                "summary": "Synthetic source establishes incompatible account ownership.",
            },
            retrieved_at=EVALUATED_AT - timedelta(hours=4),
            expires_at=EVALUATED_AT + timedelta(days=5),
        )

        claim = store.add_claim(
            subject_id=subject.id,
            statement="Synthetic portfolio lists the confirmed email address.",
            confidence=0.8,
            origin=ClaimOrigin.HUMAN,
        )
        store.link_evidence(
            claim_id=claim.id,
            observation_id=email_proof.id,
            relation=EvidenceRelation.SUPPORTS,
            rationale="Direct synthetic source text.",
        )
        store.link_evidence(
            claim_id=claim.id,
            observation_id=contradiction.id,
            relation=EvidenceRelation.UNRESOLVED,
            rationale="Contradiction remains visible for operator review.",
        )

        correlation = CorrelationEngine(session)
        same_handle_result = correlation.correlate(
            CorrelationRequest(
                subject_id=subject.id,
                candidate_observation_id=same_handle_candidate.id,
                evaluated_at=EVALUATED_AT,
                factors=(
                    CorrelationFactorInput(
                        kind=FactorKind.SAME_USERNAME,
                        observation_ids=(same_handle_candidate.id,),
                        rationale="Same public handle only.",
                    ),
                ),
            )
        )
        contradicted_result = correlation.correlate(
            CorrelationRequest(
                subject_id=subject.id,
                candidate_observation_id=contradicted_candidate.id,
                evaluated_at=EVALUATED_AT,
                factors=(
                    CorrelationFactorInput(
                        kind=FactorKind.EXACT_CONFIRMED_IDENTIFIER_OVERLAP,
                        observation_ids=(email_proof.id,),
                        identifier_ids=(email.id,),
                        rationale="Synthetic confirmed email overlap.",
                    ),
                    CorrelationFactorInput(
                        kind=FactorKind.INDEPENDENT_CROSS_LINK,
                        observation_ids=(stale_cross_link.id,),
                        rationale="Synthetic cross-link is stale.",
                    ),
                    CorrelationFactorInput(
                        kind=FactorKind.HARD_CONTRADICTION,
                        observation_ids=(contradiction.id,),
                        rationale="Synthetic hard contradiction.",
                    ),
                ),
            )
        )
        session.commit()

        yield {
            "session": session,
            "subject": subject,
            "same_handle_candidate": same_handle_candidate,
            "contradicted_candidate": contradicted_candidate,
            "stale_cross_link": stale_cross_link,
            "claim": claim,
            "same_handle_result": same_handle_result,
            "contradicted_result": contradicted_result,
        }


def test_read_model_preserves_m5_semantics_and_evidence_separation(synthetic_case) -> None:
    case = synthetic_case
    model = CaseReadModelService(case["session"]).build(
        case["subject"].id,
        at=EVALUATED_AT,
    )

    assert model.schema_version == M6_READ_MODEL_VERSION
    assert model.display_name == "Synthetic M6 Subject"
    assert len(model.claims) == 1
    assert model.claims[0].statement.startswith("Synthetic portfolio")
    assert {link.relation for link in model.claims[0].evidence_links} == {
        EvidenceRelation.SUPPORTS,
        EvidenceRelation.UNRESOLVED,
    }

    candidates = {candidate.site: candidate for candidate in model.account_candidates}
    same_handle = candidates["GitHub"].correlation
    assert same_handle is not None
    assert same_handle.outcome is CorrelationOutcome.INSUFFICIENT_EVIDENCE
    assert same_handle.evidence_score == 10
    assert same_handle.calibration_status.value == "uncalibrated"
    assert same_handle.is_identity_claim is False

    contradicted = candidates["Reddit"].correlation
    assert contradicted is not None
    assert contradicted.outcome is CorrelationOutcome.CONTRADICTED
    assert contradicted.evidence_score == 0
    assert contradicted.calibration_status.value == "uncalibrated"
    assert contradicted.is_identity_claim is False
    assert any(factor.veto for factor in contradicted.factors)
    assert any(
        factor.status is FactorStatus.EXCLUDED_STALE
        for factor in contradicted.factors
    )

    stale = next(
        item for item in model.observations if item.id == case["stale_cross_link"].id
    )
    assert stale.freshness is FreshnessState.STALE

    rendered = model.model_dump_json()
    assert "must-not-enter-read-model" not in rendered
    assert '"payload"' not in rendered


def test_every_factor_references_visible_case_evidence(synthetic_case) -> None:
    case = synthetic_case
    model = CaseReadModelService(case["session"]).build(
        case["subject"].id,
        at=EVALUATED_AT,
    )

    visible_observations = {item.id for item in model.observations}
    visible_identifiers = {item.id for item in model.identifiers}
    for candidate in model.account_candidates:
        if candidate.correlation is None:
            continue
        for factor in candidate.correlation.factors:
            assert set(factor.observation_ids).issubset(visible_observations)
            assert set(factor.identifier_ids).issubset(visible_identifiers)


def test_read_model_is_deterministic_for_same_database_state_and_time(synthetic_case) -> None:
    case = synthetic_case
    service = CaseReadModelService(case["session"])

    first = service.build(case["subject"].id, at=EVALUATED_AT)
    second = service.build(case["subject"].id, at=EVALUATED_AT)

    assert first.model_dump(mode="json") == second.model_dump(mode="json")


def test_read_model_rejects_naive_clock(synthetic_case) -> None:
    case = synthetic_case
    with pytest.raises(DashboardReadModelError, match="timezone-aware"):
        CaseReadModelService(case["session"]).build(
            case["subject"].id,
            at=datetime(2026, 8, 16, 10, 0),
        )


def test_read_model_verifies_stored_m5_output_digest(synthetic_case) -> None:
    case = synthetic_case
    run = case["session"].get(
        CorrelationRun,
        case["same_handle_result"].run_id,
    )
    run.normalized_output += " "
    case["session"].flush()

    with pytest.raises(DashboardReadModelError, match="digest does not match"):
        CaseReadModelService(case["session"]).build(
            case["subject"].id,
            at=EVALUATED_AT,
        )


def test_read_model_rejects_identity_claim_drift_even_with_matching_digest(
    synthetic_case,
) -> None:
    case = synthetic_case
    run = case["session"].get(
        CorrelationRun,
        case["same_handle_result"].run_id,
    )
    payload = json.loads(run.normalized_output)
    payload["is_identity_claim"] = True
    run.normalized_output = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    run.output_digest = hashlib.sha256(run.normalized_output.encode("utf-8")).hexdigest()
    case["session"].flush()

    with pytest.raises(DashboardReadModelError, match="must not become an identity claim"):
        CaseReadModelService(case["session"]).build(
            case["subject"].id,
            at=EVALUATED_AT,
        )


def test_m6_keeps_no_browser_facing_dashboard_http_endpoint() -> None:
    paths = {route.path for route in app.routes if hasattr(route, "path")}
    assert not any(path.startswith("/v1/dashboard") for path in paths)
