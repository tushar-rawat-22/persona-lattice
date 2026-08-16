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


def _observation(
    store,
    subject_id,
    name,
    *,
    candidate_id=None,
    stale=False,
    confirmed_identifier_ids=(),
):
    retrieved = EVALUATED_AT - timedelta(days=10)
    expires = EVALUATED_AT - timedelta(days=1) if stale else EVALUATED_AT + timedelta(days=10)
    payload = {"synthetic": True}
    if candidate_id is not None:
        payload["candidate_observation_id"] = str(candidate_id)
    if confirmed_identifier_ids:
        payload["confirmed_identifier_ids"] = [str(value) for value in confirmed_identifier_ids]
    return store.add_observation(
        subject_id=subject_id,
        source_kind=ObservationSourceKind.PUBLIC_WEB,
        source_name=name,
        source_locator=f"https://example.test/{name}",
        payload=payload,
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
    assert result.factors[0].independence_group == "provider:sherlock"
    assert json.loads(result.normalized_output)["is_identity_claim"] is False


def test_duplicate_source_group_is_derived_and_cannot_inflate_score(case) -> None:
    session, store, subject, _username, candidate = case
    source_a = _observation(store, subject.id, "mirror-a", candidate_id=candidate.id)
    source_b = _observation(store, subject.id, "mirror-b", candidate_id=candidate.id)

    result = CorrelationEngine(session).correlate(
        _request(
            subject.id,
            candidate.id,
            CorrelationFactorInput(
                FactorKind.INDEPENDENT_CROSS_LINK,
                (source_a.id,),
                rationale="Synthetic direct cross-link.",
            ),
            CorrelationFactorInput(
                FactorKind.COMPATIBLE_PROFILE_METADATA,
                (source_b.id,),
                rationale="Mirrored metadata from the same host family.",
            ),
        )
    )

    assert result.evidence_score == 35
    assert result.outcome is CorrelationOutcome.POSSIBLE_MATCH
    assert result.positive_independence_groups == 1
    assert {factor.independence_group for factor in result.factors} == {"host:example.test"}
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
    email_source = _observation(
        store,
        subject.id,
        "email-proof",
        candidate_id=candidate.id,
        confirmed_identifier_ids=(email.id,),
    )
    cross_link = store.add_observation(
        subject_id=subject.id,
        source_kind=ObservationSourceKind.PUBLIC_WEB,
        source_name="independent-cross-link",
        source_locator="https://independent.test/link",
        payload={"candidate_observation_id": str(candidate.id), "synthetic": True},
        retrieved_at=EVALUATED_AT - timedelta(days=1),
        expires_at=EVALUATED_AT + timedelta(days=10),
    )
    contradiction = store.add_observation(
        subject_id=subject.id,
        source_kind=ObservationSourceKind.PUBLIC_WEB,
        source_name="hard-contradiction",
        source_locator="https://contradiction.test/fact",
        payload={"candidate_observation_id": str(candidate.id), "synthetic": True},
        retrieved_at=EVALUATED_AT - timedelta(days=1),
        expires_at=EVALUATED_AT + timedelta(days=10),
    )

    result = CorrelationEngine(session).correlate(
        _request(
            subject.id,
            candidate.id,
            CorrelationFactorInput(
                FactorKind.EXACT_CONFIRMED_IDENTIFIER_OVERLAP,
                (email_source.id,),
                identifier_ids=(email.id,),
                rationale="Synthetic exact non-username identifier overlap.",
            ),
            CorrelationFactorInput(
                FactorKind.INDEPENDENT_CROSS_LINK,
                (cross_link.id,),
                rationale="Independent synthetic cross-link.",
            ),
            CorrelationFactorInput(
                FactorKind.HARD_CONTRADICTION,
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
    stale = _observation(
        store,
        subject.id,
        "stale-source",
        candidate_id=candidate.id,
        stale=True,
    )

    result = CorrelationEngine(session).correlate(
        _request(
            subject.id,
            candidate.id,
            CorrelationFactorInput(
                FactorKind.INDEPENDENT_CROSS_LINK,
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
    email_source = store.add_observation(
        subject_id=subject.id,
        source_kind=ObservationSourceKind.PUBLIC_WEB,
        source_name="stable-email-source",
        source_locator="https://email-proof.test/profile",
        payload={
            "candidate_observation_id": str(candidate.id),
            "confirmed_identifier_ids": [str(email.id)],
            "synthetic": True,
        },
        retrieved_at=EVALUATED_AT - timedelta(days=1),
        expires_at=EVALUATED_AT + timedelta(days=10),
    )
    cross_link = store.add_observation(
        subject_id=subject.id,
        source_kind=ObservationSourceKind.PUBLIC_WEB,
        source_name="stable-cross-link",
        source_locator="https://cross-link.test/profile",
        payload={"candidate_observation_id": str(candidate.id), "synthetic": True},
        retrieved_at=EVALUATED_AT - timedelta(days=1),
        expires_at=EVALUATED_AT + timedelta(days=10),
    )
    factor_a = CorrelationFactorInput(
        FactorKind.EXACT_CONFIRMED_IDENTIFIER_OVERLAP,
        (email_source.id,),
        identifier_ids=(email.id,),
        rationale="Stable exact overlap.",
    )
    factor_b = CorrelationFactorInput(
        FactorKind.INDEPENDENT_CROSS_LINK,
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
    session, store, subject, username, candidate = case
    source = _observation(
        store,
        subject.id,
        "username-proof",
        candidate_id=candidate.id,
        confirmed_identifier_ids=(username.id,),
    )
    with pytest.raises(CorrelationValidationError, match="Username reuse"):
        CorrelationEngine(session).correlate(
            _request(
                subject.id,
                candidate.id,
                CorrelationFactorInput(
                    FactorKind.EXACT_CONFIRMED_IDENTIFIER_OVERLAP,
                    (source.id,),
                    identifier_ids=(username.id,),
                ),
            )
        )


def test_exact_overlap_requires_candidate_bound_source_confirmation(case) -> None:
    session, store, subject, _username, candidate = case
    email = store.add_identifier(
        subject.id,
        normalize_identifier(IdentifierKind.EMAIL, "unbound@example.test"),
    )
    unbound = _observation(store, subject.id, "unbound-source")

    with pytest.raises(CorrelationValidationError, match="explicitly bound"):
        CorrelationEngine(session).correlate(
            _request(
                subject.id,
                candidate.id,
                CorrelationFactorInput(
                    FactorKind.EXACT_CONFIRMED_IDENTIFIER_OVERLAP,
                    (unbound.id,),
                    identifier_ids=(email.id,),
                ),
            )
        )


def test_cross_subject_factor_and_non_candidate_are_rejected(case) -> None:
    session, store, subject, _username, candidate = case
    other = store.add_subject("Other Synthetic Subject")
    foreign = _observation(store, other.id, "foreign-source", candidate_id=candidate.id)

    with pytest.raises(CorrelationValidationError, match="does not belong"):
        CorrelationEngine(session).correlate(
            _request(
                subject.id,
                candidate.id,
                CorrelationFactorInput(
                    FactorKind.INDEPENDENT_CROSS_LINK,
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
                    (not_candidate.id,),
                ),
            )
        )
