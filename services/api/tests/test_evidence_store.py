# SPDX-License-Identifier: Apache-2.0
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.evidence import (
    ClaimOrigin,
    EvidenceInvariantError,
    EvidenceRelation,
    EvidenceStore,
    EntityNotFound,
    FreshnessState,
    IdentifierKind,
    ObservationSourceKind,
    create_database_engine,
    create_schema,
    make_session_factory,
    normalize_identifier,
)


@pytest.fixture
def store() -> EvidenceStore:
    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    create_schema(engine)
    factory = make_session_factory(engine)
    with factory() as session:
        yield EvidenceStore(session)


def test_identifier_deduplication_and_conflicts(store: EvidenceStore) -> None:
    subject = store.add_subject("Synthetic Person")

    first = store.add_identifier(
        subject.id,
        normalize_identifier(IdentifierKind.EMAIL, "A@Example.com"),
    )
    duplicate = store.add_identifier(
        subject.id,
        normalize_identifier(IdentifierKind.EMAIL, "A@example.com"),
    )
    case_distinct = store.add_identifier(
        subject.id,
        normalize_identifier(IdentifierKind.EMAIL, "a@example.com"),
    )
    conflicting = store.add_identifier(
        subject.id,
        normalize_identifier(IdentifierKind.EMAIL, "other@example.com"),
    )

    assert duplicate.id == first.id
    assert case_distinct.id != first.id
    assert conflicting.id != first.id


def test_observations_require_provenance_and_ai_is_not_a_source(
    store: EvidenceStore,
) -> None:
    subject = store.add_subject()

    with pytest.raises(EvidenceInvariantError):
        store.add_observation(
            subject_id=subject.id,
            source_kind=ObservationSourceKind.PUBLIC_WEB,
            source_name="",
            source_locator="https://example.test/source",
            payload={},
        )

    with pytest.raises(EvidenceInvariantError):
        store.add_observation(
            subject_id=subject.id,
            source_kind="ai",  # type: ignore[arg-type]
            source_name="model",
            source_locator="analysis",
            payload={},
        )


def test_ai_claim_can_reference_real_observation(store: EvidenceStore) -> None:
    subject = store.add_subject()
    observation = store.add_observation(
        subject_id=subject.id,
        source_kind=ObservationSourceKind.PUBLIC_DOCUMENT,
        source_name="Synthetic public document",
        source_locator="https://example.test/document",
        payload={"claim": "Synthetic Person worked at Example Co."},
    )
    claim = store.add_claim(
        subject_id=subject.id,
        statement="The subject may have worked at Example Co.",
        confidence=0.72,
        origin=ClaimOrigin.AI,
    )

    link = store.link_evidence(
        claim_id=claim.id,
        observation_id=observation.id,
        relation=EvidenceRelation.SUPPORTS,
        rationale="The source explicitly names the employer.",
    )

    assert link.claim_id == claim.id
    assert link.observation_id == observation.id


def test_evidence_link_rejects_missing_and_cross_subject_entities(
    store: EvidenceStore,
) -> None:
    first_subject = store.add_subject("Synthetic One")
    second_subject = store.add_subject("Synthetic Two")

    claim = store.add_claim(
        subject_id=first_subject.id,
        statement="Synthetic claim",
        confidence=0.5,
        origin=ClaimOrigin.HUMAN,
    )
    observation = store.add_observation(
        subject_id=second_subject.id,
        source_kind=ObservationSourceKind.USER_SUPPLIED,
        source_name="Synthetic intake",
        source_locator="case://synthetic-two",
        payload={},
    )

    with pytest.raises(EntityNotFound):
        store.link_evidence(
            claim_id=claim.id,
            observation_id=uuid4(),
            relation=EvidenceRelation.UNRESOLVED,
        )

    with pytest.raises(EvidenceInvariantError):
        store.link_evidence(
            claim_id=claim.id,
            observation_id=observation.id,
            relation=EvidenceRelation.CONTRADICTS,
        )


def test_observation_freshness(store: EvidenceStore) -> None:
    subject = store.add_subject()
    now = datetime(2026, 8, 16, tzinfo=timezone.utc)

    fresh = store.add_observation(
        subject_id=subject.id,
        source_kind=ObservationSourceKind.REGISTRY,
        source_name="Synthetic registry",
        source_locator="registry://example/record/1",
        payload={},
        retrieved_at=now,
        expires_at=now + timedelta(days=1),
    )
    stale = store.add_observation(
        subject_id=subject.id,
        source_kind=ObservationSourceKind.PUBLIC_WEB,
        source_name="Synthetic page",
        source_locator="https://example.test/page",
        payload={},
        retrieved_at=now - timedelta(days=2),
        expires_at=now - timedelta(days=1),
    )
    unknown = store.add_observation(
        subject_id=subject.id,
        source_kind=ObservationSourceKind.UPLOAD,
        source_name="Synthetic upload",
        source_locator="upload://fixture",
        payload={},
        retrieved_at=now,
    )

    assert fresh.freshness(now) is FreshnessState.FRESH
    assert stale.freshness(now) is FreshnessState.STALE
    assert unknown.freshness(now) is FreshnessState.UNKNOWN
