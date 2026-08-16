# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json

import pytest
from sqlalchemy import func, select

from app.correlation import (
    CalibrationStatus,
    CorrelationEngine,
    CorrelationFactorInput,
    CorrelationOutcome,
    CorrelationRequest,
    CorrelationValidationError,
    FactorKind,
    FactorStatus,
    M5_POLICY_VERSION,
)
from app.correlation.models import CorrelationFactorRecord, CorrelationRun
from app.evidence import (
    EvidenceStore,
    IdentifierKind,
    ObservationSourceKind,
    create_database_engine,
    create_schema,
    make_session_factory,
    normalize_identifier,
)

EVALUATED_AT = datetime(2026, 8, 16, 8, 0, tzinfo=timezone.utc)


@pytest.fixture
def case():
    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    create_schema(engine)
    factory = make_session_factory(engine)
    with factory() as session:
        store = EvidenceStore(session)
        subject = store.add_subject("Synthetic Subject")
        username = store.add_identifier(
            subject.id,
            normalize_identifier(IdentifierKind.USERNAME, "synthetic-handle"),
        )
        candidate = store.add_observation(
            subject_id=subject.id,
            identifier_id=username.id,
            source_kind=ObservationSourceKind.PROVIDER,
            source_name="sherlock",
            source_locator="https://github.com/synthetic-handle",
            payload={
                "account_candidate": True,
                "identity_claim": False,
                "site": "GitHub",
            },
            retrieved_at=EVALUATED_AT - timedelta(days=1),
        )
        yield session, store, subject, username, candidate


def _observation(store, subject_id, name, *, stale=False):
    retrieved = EVALUATED_AT - timedelta(days=10)
    expires = EVALUATED_AT - timedelta(days=1) if stale else EVALUATED_AT + timedelta(days=10)
    return store.add_observation(
        subject_id=subject_id,
        source_kind=ObservationSourceKind.PUBLIC_WEB,
        source_name=name,
        source_locator=f"https://example.test/{name}",
        payload={"synthetic": True},
        retrieved_at=retrieved,
        expires_at=expires,
    )


def _request(subject_id, candidate_id, *factors):
    return CorrelationRequest(
        subject_id=subject_id,
        candidate_observation_id=candidate_id,
        evaluated_at=EVALUATED_AT,
        factors=tuple(factors),
    )


def test_same_username_only_is_insufficient_and_uncalibrated(case) -> None:
    session, _store, subject, _username, candidate = case
    result = CorrelationEngine(session).correlate(
        _request(
            subject.id,
            candidate.id,
            CorrelationFactorInput(
                kind=FactorKind.SAME_USERNAME,
                independence_group="sherlock:github",
                observation_ids=(candidate.id,),
                rationale="The same public handle exists.",
            ),
        )
    )

    assert result.policy_version == M5_POLICY_VERSION
    assert result.outcome is CorrelationOutcome.INSUFFICIENT_EVIDENCE
    assert result.evidence_score == 10
    assert result.calibration_status is CalibrationStatus.UNCALIBRATED
    assert result.is_identity_claim is False
    assert json.loads(result.normalized_output)["is_identity_claim"] is False


def test_duplicate_independence_group_cannot_inflate_score(case) -> None:
    session, store, subject, _username, candidate = case
    source_a = _observation(store, subject.id, "mirror-a")
    source_b = _observation(store, subject.id, "mirror-b")

    result = CorrelationEngine(session).correlate(
        _request(
            subject.id,
            candidate.id,
            CorrelationFactorInput(
                FactorKind.INDEPENDENT_CROSS_LINK,
                "same-publisher-network",
                (source_a.id,),
                rationale="Synthetic direct cross-link.",
            ),
            CorrelationFactorInput(
                FactorKind.COMPATIBLE_PROFILE_METADATA,
                "same-publisher-network",
                (source_b.id,),
                rationale="Mirrored metadata from the same evidence family.",
            ),
        )
    )

    assert result.evidence_score == 35
    assert result.outcome is CorrelationOutcome.POSSIBLE_MATCH
    assert result.positive_independence_groups == 1
    assert sorted(factor.applied_weight for factor in result.factors) == [0, 35]
    assert any(
        factor.status is FactorStatus.SUPPRESSED_SAME_INDEPENDENCE_GROUP
        for factor in result.factors
    )


def test_hard_contradiction_vetoes_otherwise_strong_evidence(case) -> None:
    session, store, subject, _username, candidate = case
    email = store.add_identifier(
        subject.id,
        normalize_identifier(IdentifierKind.EMAIL, "synthetic@example.test"),
    )
    cross_link = _observation(store, subject.id, "independent-cross-link")
    contradiction = _observation(store, subject.id, "hard-contradiction")

    result = CorrelationEngine(session).correlate(
        _request(
            subject.id,
            candidate.id,
            CorrelationFactorInput(
                FactorKind.EXACT_CONFIRMED_IDENTIFIER_OVERLAP,
                "confirmed-email",
                identifier_ids=(email.id,),
                rationale="Synthetic exact non-username identifier overlap.",
            ),
            CorrelationFactorInput(
                FactorKind.INDEPENDENT_CROSS_LINK,
                "independent-site",
                (cross_link.id,),
                rationale="Independent synthetic cross-link.",
            ),
            CorrelationFactorInput(
                FactorKind.HARD_CONTRADICTION,
                "contradiction-source",
                (contradiction.id,),
                rationale="Synthetic evidence proves the candidate is incompatible.",
            ),
        )
    )

    assert result.outcome is CorrelationOutcome.CONTRADICTED
    assert result.evidence_score == 0
    assert any(factor.veto and factor.applied_weight == -100 for factor in result.factors)


def test_stale_evidence_is_visible_but_excluded(case) -> None:
    session, store, subject, _username, candidate = case
    stale = _observation(store, subject.id, "stale-source", stale=True)

    result = CorrelationEngine(session).correlate(
        _request(
            subject.id,
            candidate.id,
            CorrelationFactorInput(
                FactorKind.INDEPENDENT_CROSS_LINK,
                "stale-independent-source",
                (stale.id,),
                rationale="This synthetic source expired before evaluation.",
            ),
        )
    )

    assert result.evidence_score == 0
    assert result.outcome is CorrelationOutcome.INSUFFICIENT_EVIDENCE
    assert result.factors[0].status is FactorStatus.EXCLUDED_STALE
    assert result.factors[0].applied_weight == 0


def test_replay_is_byte_stable_order_independent_and_persisted_once(case) -> None:
    session, store, subject, _username, candidate = case
    email = store.add_identifier(
        subject.id,
        normalize_identifier(IdentifierKind.EMAIL, "stable@example.test"),
    )
    cross_link = _observation(store, subject.id, "stable-cross-link")
    factor_a = CorrelationFactorInput(
        FactorKind.EXACT_CONFIRMED_IDENTIFIER_OVERLAP,
        "confirmed-email",
        identifier_ids=(email.id,),
        rationale="Stable exact overlap.",
    )
    factor_b = CorrelationFactorInput(
        FactorKind.INDEPENDENT_CROSS_LINK,
        "independent-link",
        (cross_link.id,),
        rationale="Stable cross-link.",
    )
    engine = CorrelationEngine(session)

    first = engine.correlate(_request(subject.id, candidate.id, factor_a, factor_b))
    second = engine.correlate(_request(subject.id, candidate.id, factor_b, factor_a))

    assert first.outcome is CorrelationOutcome.STRONG_CANDIDATE
    assert first.evidence_score == 90
    assert first.normalized_output == second.normalized_output
    assert first.output_digest == second.output_digest
    assert first.input_digest == second.input_digest
    assert first.run_id == second.run_id
    assert session.scalar(select(func.count()).select_from(CorrelationRun)) == 1
    assert session.scalar(select(func.count()).select_from(CorrelationFactorRecord)) == 2


def test_username_cannot_be_upgraded_to_exact_confirmed_overlap(case) -> None:
    session, _store, subject, username, candidate = case
    with pytest.raises(CorrelationValidationError, match="Username reuse"):
        CorrelationEngine(session).correlate(
            _request(
                subject.id,
                candidate.id,
                CorrelationFactorInput(
                    FactorKind.EXACT_CONFIRMED_IDENTIFIER_OVERLAP,
                    "bad-upgrade",
                    identifier_ids=(username.id,),
                ),
            )
        )


def test_cross_subject_factor_and_non_candidate_are_rejected(case) -> None:
    session, store, subject, _username, candidate = case
    other = store.add_subject("Other Synthetic Subject")
    foreign = _observation(store, other.id, "foreign-source")

    with pytest.raises(CorrelationValidationError, match="does not belong"):
        CorrelationEngine(session).correlate(
            _request(
                subject.id,
                candidate.id,
                CorrelationFactorInput(
                    FactorKind.INDEPENDENT_CROSS_LINK,
                    "foreign",
                    (foreign.id,),
                ),
            )
        )

    not_candidate = _observation(store, subject.id, "ordinary-observation")
    with pytest.raises(CorrelationValidationError, match="not an account candidate"):
        CorrelationEngine(session).correlate(
            _request(
                subject.id,
                not_candidate.id,
                CorrelationFactorInput(
                    FactorKind.SAME_USERNAME,
                    "ordinary",
                    (not_candidate.id,),
                ),
            )
        )
