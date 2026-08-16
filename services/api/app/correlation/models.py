# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.evidence.models import Base, utcnow


class CorrelationRun(Base):
    __tablename__ = "correlation_runs"
    __table_args__ = (
        UniqueConstraint(
            "subject_id",
            "candidate_observation_id",
            "policy_version",
            "input_digest",
            name="uq_correlation_run_replay",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    subject_id: Mapped[UUID] = mapped_column(
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    candidate_observation_id: Mapped[UUID] = mapped_column(
        ForeignKey("observations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    policy_version: Mapped[str] = mapped_column(String(80), nullable=False)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    input_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    output_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    normalized_output: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    factors: Mapped[list[CorrelationFactorRecord]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="CorrelationFactorRecord.ordinal",
    )


class CorrelationFactorRecord(Base):
    __tablename__ = "correlation_factor_records"
    __table_args__ = (
        UniqueConstraint("run_id", "ordinal", name="uq_correlation_factor_run_ordinal"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    run_id: Mapped[UUID] = mapped_column(
        ForeignKey("correlation_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    kind: Mapped[str] = mapped_column(String(80), nullable=False)
    independence_group: Mapped[str] = mapped_column(String(120), nullable=False)
    base_weight: Mapped[int] = mapped_column(Integer, nullable=False)
    applied_weight: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(80), nullable=False)
    veto: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    observation_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    identifier_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    rationale: Mapped[str] = mapped_column(Text, nullable=False, default="")

    run: Mapped[CorrelationRun] = relationship(back_populates="factors")
