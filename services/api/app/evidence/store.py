# SPDX-License-Identifier: Apache-2.0
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Claim, EvidenceLink, Identifier, Observation, Subject, utcnow
from .normalization import NormalizedIdentifier
from .types import ClaimOrigin, EvidenceRelation, ObservationSourceKind


class EvidenceStoreError(RuntimeError):
    pass


class EntityNotFound(EvidenceStoreError):
    pass


class EvidenceInvariantError(EvidenceStoreError):
    pass


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class EvidenceStore:
    def __init__(self, session: Session):
        self.session = session

    def add_subject(self, display_name: str | None = None) -> Subject:
        subject = Subject(display_name=display_name.strip() if display_name else None)
        self.session.add(subject)
        self.session.flush()
        return subject

    def get_subject(self, subject_id: UUID) -> Subject:
        subject = self.session.get(Subject, subject_id)
        if subject is None:
            raise EntityNotFound(f"Subject {subject_id} does not exist.")
        return subject

    def get_identifier(self, identifier_id: UUID) -> Identifier:
        identifier = self.session.get(Identifier, identifier_id)
        if identifier is None:
            raise EntityNotFound(f"Identifier {identifier_id} does not exist.")
        return identifier

    def add_identifier(
        self,
        subject_id: UUID,
        normalized: NormalizedIdentifier,
    ) -> Identifier:
        self.get_subject(subject_id)

        existing = self.session.scalar(
            select(Identifier).where(
                Identifier.subject_id == subject_id,
                Identifier.kind == normalized.kind,
                Identifier.comparison_key == normalized.comparison_key,
            )
        )
        if existing is not None:
            return existing

        identifier = Identifier(
            subject_id=subject_id,
            kind=normalized.kind,
            raw_value=normalized.raw_value,
            normalized_value=normalized.normalized_value,
            comparison_key=normalized.comparison_key,
        )
        self.session.add(identifier)
        self.session.flush()
        return identifier

    def add_observation(
        self,
        *,
        subject_id: UUID,
        source_kind: ObservationSourceKind,
        source_name: str,
        source_locator: str,
        payload: dict[str, Any],
        retrieved_at: datetime | None = None,
        identifier_id: UUID | None = None,
        observed_at: datetime | None = None,
        expires_at: datetime | None = None,
    ) -> Observation:
        subject = self.get_subject(subject_id)

        try:
            source_kind = ObservationSourceKind(source_kind)
        except ValueError as exc:
            raise EvidenceInvariantError(
                "Observations require a recognized non-AI source kind."
            ) from exc

        if not source_name.strip():
            raise EvidenceInvariantError("Observation source_name is required.")
        if not source_locator.strip():
            raise EvidenceInvariantError("Observation source_locator is required.")

        if identifier_id is not None:
            identifier = self.get_identifier(identifier_id)
            if identifier.subject_id != subject.id:
                raise EvidenceInvariantError(
                    "Observation identifier must belong to the same subject."
                )

        retrieved = _as_utc(retrieved_at or utcnow())
        observed = _as_utc(observed_at) if observed_at else None
        expires = _as_utc(expires_at) if expires_at else None

        if expires is not None and expires < retrieved:
            raise EvidenceInvariantError("Observation expires_at cannot precede retrieved_at.")

        observation = Observation(
            subject_id=subject.id,
            identifier_id=identifier_id,
            source_kind=source_kind,
            source_name=source_name.strip(),
            source_locator=source_locator.strip(),
            payload=payload,
            retrieved_at=retrieved,
            observed_at=observed,
            expires_at=expires,
        )
        self.session.add(observation)
        self.session.flush()
        return observation

    def add_claim(
        self,
        *,
        subject_id: UUID,
        statement: str,
        confidence: float,
        origin: ClaimOrigin,
    ) -> Claim:
        self.get_subject(subject_id)

        if not statement.strip():
            raise EvidenceInvariantError("Claim statement is required.")
        if not 0.0 <= confidence <= 1.0:
            raise EvidenceInvariantError("Claim confidence must be between 0 and 1.")

        try:
            origin = ClaimOrigin(origin)
        except ValueError as exc:
            raise EvidenceInvariantError("Claim origin is not recognized.") from exc

        claim = Claim(
            subject_id=subject_id,
            statement=statement.strip(),
            confidence=confidence,
            origin=origin,
        )
        self.session.add(claim)
        self.session.flush()
        return claim

    def link_evidence(
        self,
        *,
        claim_id: UUID,
        observation_id: UUID,
        relation: EvidenceRelation,
        rationale: str | None = None,
    ) -> EvidenceLink:
        claim = self.session.get(Claim, claim_id)
        if claim is None:
            raise EntityNotFound(f"Claim {claim_id} does not exist.")

        observation = self.session.get(Observation, observation_id)
        if observation is None:
            raise EntityNotFound(f"Observation {observation_id} does not exist.")

        if claim.subject_id != observation.subject_id:
            raise EvidenceInvariantError(
                "Claim and observation must belong to the same subject."
            )

        try:
            relation = EvidenceRelation(relation)
        except ValueError as exc:
            raise EvidenceInvariantError("Evidence relation is not recognized.") from exc

        existing = self.session.scalar(
            select(EvidenceLink).where(
                EvidenceLink.claim_id == claim_id,
                EvidenceLink.observation_id == observation_id,
                EvidenceLink.relation == relation,
            )
        )
        if existing is not None:
            return existing

        link = EvidenceLink(
            claim_id=claim_id,
            observation_id=observation_id,
            relation=relation,
            rationale=rationale.strip() if rationale else None,
        )
        self.session.add(link)
        self.session.flush()
        return link
