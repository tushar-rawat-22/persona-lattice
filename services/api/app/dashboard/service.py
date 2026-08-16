# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.correlation import (
    CalibrationStatus,
    CorrelationOutcome,
    FactorKind,
    FactorStatus,
)
from app.correlation.models import CorrelationRun
from app.evidence.models import Claim, EvidenceLink, Observation, Subject, utcnow

from .types import (
    AccountCandidateView,
    CaseReadModel,
    ClaimView,
    CorrelationFactorView,
    CorrelationView,
    EvidenceLinkView,
    IdentifierView,
    ObservationView,
    ProvenanceView,
)

M6_READ_MODEL_VERSION = "m6-case-read-model-v1"

MAX_IDENTIFIERS = 128
MAX_OBSERVATIONS = 512
MAX_CLAIMS = 256
MAX_ACCOUNT_CANDIDATES = 128
MAX_EVIDENCE_LINKS_PER_CLAIM = 128
MAX_CORRELATION_FACTORS = 64

MAX_IDENTIFIER_CHARS = 2048
MAX_SOURCE_NAME_CHARS = 120
MAX_SOURCE_LOCATOR_CHARS = 2048
MAX_SUMMARY_CHARS = 180
MAX_SITE_CHARS = 120
MAX_CLAIM_CHARS = 2000
MAX_RATIONALE_CHARS = 500


class DashboardReadModelError(RuntimeError):
    pass


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _required_aware(value: datetime | None) -> datetime:
    if value is None:
        return utcnow()
    if value.tzinfo is None:
        raise DashboardReadModelError("Dashboard read-model time must be timezone-aware.")
    return value.astimezone(timezone.utc)


def _ensure_count(label: str, count: int, limit: int) -> None:
    if count > limit:
        raise DashboardReadModelError(
            f"Case has {count} {label}; M6 read-model limit is {limit}."
        )


def _required_text(value: object, field: str, max_chars: int) -> str:
    if not isinstance(value, str):
        raise DashboardReadModelError(f"{field} must be stored as text.")
    if not value.strip():
        raise DashboardReadModelError(f"{field} must not be blank.")
    if len(value) > max_chars:
        raise DashboardReadModelError(
            f"{field} exceeds the M6 read-model limit of {max_chars} characters."
        )
    return value


def _optional_text(value: object, field: str, max_chars: int) -> str | None:
    if value is None:
        return None
    return _required_text(value, field, max_chars)


def _bounded_display_text(value: object, max_chars: int) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = " ".join(value.split())
    if not normalized:
        return None
    if len(normalized) <= max_chars:
        return normalized
    return normalized[: max_chars - 1].rstrip() + "…"


def _observation_summary(observation: Observation) -> str:
    parts: list[str] = []
    for key in ("site", "status", "title", "summary"):
        item = _bounded_display_text(observation.payload.get(key), MAX_SUMMARY_CHARS)
        if item and item not in parts:
            parts.append(item)
    if parts:
        joined = " · ".join(parts)
        return _bounded_display_text(joined, MAX_SUMMARY_CHARS) or "Source observation"
    fallback = f"{observation.source_kind.value} observation from {observation.source_name}"
    return _bounded_display_text(fallback, MAX_SUMMARY_CHARS) or "Source observation"


def _strict_string(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise DashboardReadModelError(f"Stored correlation {field} is invalid.")
    return value


def _strict_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise DashboardReadModelError(f"Stored correlation {field} is invalid.")
    return value


def _strict_bool(value: object, field: str) -> bool:
    if type(value) is not bool:
        raise DashboardReadModelError(f"Stored correlation {field} is invalid.")
    return value


def _uuid_from_payload(value: object, field: str) -> UUID:
    if not isinstance(value, str):
        raise DashboardReadModelError(f"Stored correlation {field} is invalid.")
    try:
        return UUID(value)
    except ValueError as exc:
        raise DashboardReadModelError(f"Stored correlation {field} is invalid.") from exc


def _datetime_from_payload(value: object, field: str) -> datetime:
    if not isinstance(value, str):
        raise DashboardReadModelError(f"Stored correlation {field} is invalid.")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise DashboardReadModelError(f"Stored correlation {field} is invalid.") from exc
    if parsed.tzinfo is None:
        raise DashboardReadModelError(f"Stored correlation {field} must be timezone-aware.")
    return parsed.astimezone(timezone.utc)


def _list_of_uuids(value: object, field: str) -> tuple[UUID, ...]:
    if not isinstance(value, list):
        raise DashboardReadModelError(f"Stored correlation {field} is invalid.")
    return tuple(_uuid_from_payload(item, field) for item in value)


def _verify_output_digest(run: CorrelationRun) -> None:
    actual = hashlib.sha256(run.normalized_output.encode("utf-8")).hexdigest()
    if actual != run.output_digest:
        raise DashboardReadModelError("Stored correlation output digest does not match its payload.")


def _correlation_view(run: CorrelationRun) -> CorrelationView:
    _verify_output_digest(run)
    try:
        payload: dict[str, Any] = json.loads(run.normalized_output)
        raw_factors = payload["factors"]
        if not isinstance(raw_factors, list):
            raise TypeError
        _ensure_count("correlation factors", len(raw_factors), MAX_CORRELATION_FACTORS)
        factors = tuple(
            CorrelationFactorView(
                kind=FactorKind(_strict_string(item["kind"], "factor.kind")),
                independence_group=_required_text(
                    item["independence_group"],
                    "Correlation independence group",
                    120,
                ),
                base_weight=_strict_int(item["base_weight"], "factor.base_weight"),
                applied_weight=_strict_int(item["applied_weight"], "factor.applied_weight"),
                status=FactorStatus(_strict_string(item["status"], "factor.status")),
                observation_ids=_list_of_uuids(
                    item["observation_ids"],
                    "factor.observation_ids",
                ),
                identifier_ids=_list_of_uuids(
                    item["identifier_ids"],
                    "factor.identifier_ids",
                ),
                rationale=_strict_string(item["rationale"], "factor.rationale"),
                veto=_strict_bool(item["veto"], "factor.veto"),
            )
            for item in raw_factors
        )
        subject_id = _uuid_from_payload(payload["subject_id"], "subject_id")
        candidate_id = _uuid_from_payload(
            payload["candidate_observation_id"],
            "candidate_observation_id",
        )
        evaluated_at = _datetime_from_payload(payload["evaluated_at"], "evaluated_at")
        policy_version = _strict_string(payload["policy_version"], "policy_version")
        result = CorrelationView(
            run_id=run.id,
            policy_version=policy_version,
            candidate_observation_id=candidate_id,
            evaluated_at=evaluated_at,
            outcome=CorrelationOutcome(_strict_string(payload["outcome"], "outcome")),
            evidence_score=_strict_int(payload["evidence_score"], "evidence_score"),
            calibration_status=CalibrationStatus(
                _strict_string(payload["calibration_status"], "calibration_status")
            ),
            positive_independence_groups=_strict_int(
                payload["positive_independence_groups"],
                "positive_independence_groups",
            ),
            factors=factors,
            is_identity_claim=_strict_bool(
                payload["is_identity_claim"],
                "is_identity_claim",
            ),
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise DashboardReadModelError("Stored correlation output is malformed.") from exc

    if subject_id != run.subject_id:
        raise DashboardReadModelError("Stored correlation subject does not match its run.")
    if result.candidate_observation_id != run.candidate_observation_id:
        raise DashboardReadModelError("Stored correlation candidate does not match its run.")
    if result.policy_version != run.policy_version:
        raise DashboardReadModelError("Stored correlation policy version does not match its run.")
    if result.evaluated_at != _as_utc(run.evaluated_at):
        raise DashboardReadModelError("Stored correlation evaluation time does not match its run.")
    if result.calibration_status is not CalibrationStatus.UNCALIBRATED:
        raise DashboardReadModelError("M5 correlation output must remain uncalibrated.")
    if result.is_identity_claim:
        raise DashboardReadModelError("M5 correlation output must not become an identity claim.")
    return result


def _latest_correlations(
    runs: list[CorrelationRun],
) -> dict[UUID, CorrelationView]:
    latest: dict[UUID, tuple[tuple[datetime, datetime, str], CorrelationView]] = {}
    for run in runs:
        view = _correlation_view(run)
        key = (_as_utc(run.evaluated_at), _as_utc(run.created_at), str(run.id))
        current = latest.get(run.candidate_observation_id)
        if current is None or key > current[0]:
            latest[run.candidate_observation_id] = (key, view)
    return {candidate_id: item[1] for candidate_id, item in latest.items()}


class CaseReadModelService:
    """Build a bounded, read-only M6 view over stored evidence.

    M6 intentionally exposes no HTTP case endpoint. The service exists so the
    synthetic local dashboard and tests share one contract while M7 retains
    responsibility for authentication, authorization and production case access.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def build(
        self,
        subject_id: UUID,
        *,
        at: datetime | None = None,
    ) -> CaseReadModel:
        generated_at = _required_aware(at)
        subject = self.session.scalar(
            select(Subject)
            .where(Subject.id == subject_id)
            .options(
                selectinload(Subject.identifiers),
                selectinload(Subject.observations),
                selectinload(Subject.claims)
                .selectinload(Claim.evidence_links)
                .selectinload(EvidenceLink.observation),
            )
        )
        if subject is None:
            raise DashboardReadModelError("Subject does not exist.")

        _ensure_count("identifiers", len(subject.identifiers), MAX_IDENTIFIERS)
        _ensure_count("observations", len(subject.observations), MAX_OBSERVATIONS)
        _ensure_count("claims", len(subject.claims), MAX_CLAIMS)

        display_name = _optional_text(
            subject.display_name,
            "Subject display name",
            200,
        )

        identifiers = tuple(
            IdentifierView(
                id=identifier.id,
                kind=identifier.kind,
                value=_required_text(
                    identifier.normalized_value,
                    "Identifier normalized value",
                    MAX_IDENTIFIER_CHARS,
                ),
            )
            for identifier in sorted(
                subject.identifiers,
                key=lambda item: (item.kind.value, item.normalized_value, str(item.id)),
            )
        )
        identifier_ids = {item.id for item in identifiers}

        observations = tuple(
            ObservationView(
                id=observation.id,
                identifier_id=observation.identifier_id,
                provenance=ProvenanceView(
                    source_kind=observation.source_kind,
                    source_name=_required_text(
                        observation.source_name,
                        "Observation source name",
                        MAX_SOURCE_NAME_CHARS,
                    ),
                    source_locator=_required_text(
                        observation.source_locator,
                        "Observation source locator",
                        MAX_SOURCE_LOCATOR_CHARS,
                    ),
                ),
                retrieved_at=_as_utc(observation.retrieved_at),
                observed_at=_as_utc(observation.observed_at) if observation.observed_at else None,
                expires_at=_as_utc(observation.expires_at) if observation.expires_at else None,
                freshness=observation.freshness(generated_at),
                summary=_observation_summary(observation),
                account_candidate=observation.payload.get("account_candidate") is True,
                identity_claim=(
                    observation.payload.get("identity_claim")
                    if type(observation.payload.get("identity_claim")) is bool
                    else None
                ),
                candidate_observation_id=(
                    _uuid_from_payload(
                        observation.payload["candidate_observation_id"],
                        "candidate_observation_id",
                    )
                    if observation.payload.get("candidate_observation_id") is not None
                    else None
                ),
            )
            for observation in sorted(
                subject.observations,
                key=lambda item: (_as_utc(item.retrieved_at), str(item.id)),
            )
        )
        observation_ids = {item.id for item in observations}

        claims: list[ClaimView] = []
        for claim in sorted(
            subject.claims,
            key=lambda item: (_as_utc(item.created_at), str(item.id)),
        ):
            _ensure_count(
                "evidence links on one claim",
                len(claim.evidence_links),
                MAX_EVIDENCE_LINKS_PER_CLAIM,
            )
            links = tuple(
                EvidenceLinkView(
                    observation_id=link.observation_id,
                    relation=link.relation,
                    rationale=_optional_text(
                        link.rationale,
                        "Evidence-link rationale",
                        MAX_RATIONALE_CHARS,
                    ),
                )
                for link in sorted(
                    claim.evidence_links,
                    key=lambda item: (
                        item.relation.value,
                        str(item.observation_id),
                        str(item.id),
                    ),
                )
            )
            if any(link.observation_id not in observation_ids for link in links):
                raise DashboardReadModelError(
                    "Claim evidence link references an observation outside the case."
                )
            claims.append(
                ClaimView(
                    id=claim.id,
                    statement=_required_text(
                        claim.statement,
                        "Claim statement",
                        MAX_CLAIM_CHARS,
                    ),
                    confidence=claim.confidence,
                    origin=claim.origin,
                    evidence_links=links,
                )
            )

        runs = list(
            self.session.scalars(
                select(CorrelationRun)
                .where(CorrelationRun.subject_id == subject_id)
                .order_by(
                    CorrelationRun.evaluated_at,
                    CorrelationRun.created_at,
                    CorrelationRun.id,
                )
            )
        )
        latest = _latest_correlations(runs)

        account_candidates: list[AccountCandidateView] = []
        candidate_ids: set[UUID] = set()
        for observation in subject.observations:
            if observation.payload.get("account_candidate") is not True:
                continue
            candidate_ids.add(observation.id)
            if observation.payload.get("identity_claim") is not False:
                raise DashboardReadModelError(
                    "Account candidate must explicitly remain non-identity evidence."
                )
            if observation.identifier_id is None or observation.identifier_id not in identifier_ids:
                raise DashboardReadModelError(
                    "Account candidate is missing its visible source identifier."
                )
            correlation = latest.get(observation.id)
            if correlation is not None:
                factor_observation_ids = {
                    observation_id
                    for factor in correlation.factors
                    for observation_id in factor.observation_ids
                }
                factor_identifier_ids = {
                    identifier_id
                    for factor in correlation.factors
                    for identifier_id in factor.identifier_ids
                }
                if not factor_observation_ids.issubset(observation_ids):
                    raise DashboardReadModelError(
                        "Correlation factor references evidence outside the case read model."
                    )
                if not factor_identifier_ids.issubset(identifier_ids):
                    raise DashboardReadModelError(
                        "Correlation factor references an identifier outside the case read model."
                    )

            account_candidates.append(
                AccountCandidateView(
                    observation_id=observation.id,
                    identifier_id=observation.identifier_id,
                    source_name=_required_text(
                        observation.source_name,
                        "Candidate source name",
                        MAX_SOURCE_NAME_CHARS,
                    ),
                    site=_bounded_display_text(
                        observation.payload.get("site"),
                        MAX_SITE_CHARS,
                    ),
                    profile_url=_required_text(
                        observation.source_locator,
                        "Candidate profile locator",
                        MAX_SOURCE_LOCATOR_CHARS,
                    ),
                    correlation=correlation,
                )
            )

        _ensure_count(
            "account candidates",
            len(account_candidates),
            MAX_ACCOUNT_CANDIDATES,
        )
        if set(latest) - candidate_ids:
            raise DashboardReadModelError(
                "Stored correlation run is not attached to a visible account candidate."
            )

        account_candidates.sort(
            key=lambda item: (
                item.site or "",
                item.source_name,
                item.profile_url,
                str(item.observation_id),
            )
        )

        return CaseReadModel(
            schema_version=M6_READ_MODEL_VERSION,
            generated_at=generated_at,
            subject_id=subject.id,
            display_name=display_name,
            identifiers=identifiers,
            observations=observations,
            claims=tuple(claims),
            account_candidates=tuple(account_candidates),
        )
