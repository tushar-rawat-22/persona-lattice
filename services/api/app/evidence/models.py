# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    Enum as SqlEnum,
    Float,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from .types import (
    ClaimOrigin,
    EvidenceRelation,
    FreshnessState,
    IdentifierKind,
    ObservationSourceKind,
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _enum_values(enum_type):
    return [item.value for item in enum_type]


class Base(DeclarativeBase):
    pass


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    display_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )

    identifiers: Mapped[list[Identifier]] = relationship(
        back_populates="subject",
        cascade="all, delete-orphan",
    )
    observations: Mapped[list[Observation]] = relationship(
        back_populates="subject",
        cascade="all, delete-orphan",
    )
    claims: Mapped[list[Claim]] = relationship(
        back_populates="subject",
        cascade="all, delete-orphan",
    )


class Identifier(Base):
    __tablename__ = "identifiers"
    __table_args__ = (
        UniqueConstraint(
            "subject_id",
            "kind",
            "comparison_key",
            name="uq_identifier_subject_kind_key",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    subject_id: Mapped[UUID] = mapped_column(
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    kind: Mapped[IdentifierKind] = mapped_column(
        SqlEnum(IdentifierKind, native_enum=False, create_constraint=True, values_callable=_enum_values),
        nullable=False,
    )
    raw_value: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_value: Mapped[str] = mapped_column(Text, nullable=False)
    comparison_key: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )

    subject: Mapped[Subject] = relationship(back_populates="identifiers")
    observations: Mapped[list[Observation]] = relationship(back_populates="identifier")


class Observation(Base):
    __tablename__ = "observations"
    __table_args__ = (
        CheckConstraint("length(trim(source_name)) > 0", name="ck_observation_source_name"),
        CheckConstraint(
            "length(trim(source_locator)) > 0",
            name="ck_observation_source_locator",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    subject_id: Mapped[UUID] = mapped_column(
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    identifier_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("identifiers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_kind: Mapped[ObservationSourceKind] = mapped_column(
        SqlEnum(ObservationSourceKind, native_enum=False, create_constraint=True, values_callable=_enum_values),
        nullable=False,
    )
    source_name: Mapped[str] = mapped_column(String(120), nullable=False)
    source_locator: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    observed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )

    subject: Mapped[Subject] = relationship(back_populates="observations")
    identifier: Mapped[Identifier | None] = relationship(back_populates="observations")
    evidence_links: Mapped[list[EvidenceLink]] = relationship(
        back_populates="observation",
        cascade="all, delete-orphan",
    )

    def freshness(self, at: datetime | None = None) -> FreshnessState:
        if self.expires_at is None:
            return FreshnessState.UNKNOWN

        check_time = _as_utc(at or utcnow())
        expiry = _as_utc(self.expires_at)
        return FreshnessState.FRESH if expiry > check_time else FreshnessState.STALE


class Claim(Base):
    __tablename__ = "claims"
    __table_args__ = (
        CheckConstraint(
            "confidence >= 0.0 AND confidence <= 1.0",
            name="ck_claim_confidence",
        ),
        CheckConstraint("length(trim(statement)) > 0", name="ck_claim_statement"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    subject_id: Mapped[UUID] = mapped_column(
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    origin: Mapped[ClaimOrigin] = mapped_column(
        SqlEnum(ClaimOrigin, native_enum=False, create_constraint=True, values_callable=_enum_values),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )

    subject: Mapped[Subject] = relationship(back_populates="claims")
    evidence_links: Mapped[list[EvidenceLink]] = relationship(
        back_populates="claim",
        cascade="all, delete-orphan",
    )


class EvidenceLink(Base):
    __tablename__ = "evidence_links"
    __table_args__ = (
        UniqueConstraint(
            "claim_id",
            "observation_id",
            "relation",
            name="uq_evidence_link_claim_observation_relation",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    claim_id: Mapped[UUID] = mapped_column(
        ForeignKey("claims.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    observation_id: Mapped[UUID] = mapped_column(
        ForeignKey("observations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    relation: Mapped[EvidenceRelation] = mapped_column(
        SqlEnum(EvidenceRelation, native_enum=False, create_constraint=True, values_callable=_enum_values),
        nullable=False,
    )
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )

    claim: Mapped[Claim] = relationship(back_populates="evidence_links")
    observation: Mapped[Observation] = relationship(back_populates="evidence_links")
