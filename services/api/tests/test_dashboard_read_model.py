# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from datetime import UTC, datetime, timedelta
import hashlib
import json
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.correlation import (
    CalibrationStatus,
    CorrelationRun,
    create_correlation_run,
)
from app.dashboard import CaseReadModelService, DashboardReadModelError
from app.evidence import (
    IdentifierKind,
    Observation,
    ObservationSourceMode,
    Subject,
    add_identifier,
    add_observation,
    create_subject,
)
from app.main import app
from app.storage import create_database_engine, create_session_factory, initialize_schema


EVALUATED_AT = datetime(2026, 3, 1, 12, 0, tzinfo=UTC)


@pytest.fixture()
def synthetic_case(tmp_path: Path) -> dict[str, object]:
    engine = create_database_engine(f"sqlite+pysqlite:///{tmp_path / 'dashboard.db'}")
    initialize_schema(engine)
    factory = create_session_factory(engine)
    session = factory()

    subject = create_subject(session, "Dashboard Test")
    username = add_identifier(session, subject.id, IdentifierKind.USERNAME, "same_handle")
    email = add_identifier(session, subject.id, IdentifierKind.EMAIL, "analyst@example.test")

    stale_observation = add_observation(
        session,
        subject.id,
        identifier_id=username.id,
        source="synthetic_stale",
        source_locator="synthetic://stale",
        observed_at=EVALUATED_AT - timedelta(days=500),
        source_mode=ObservationSourceMode.SYNTHETIC,
        normalized_payload={"username": "same_handle"},
    )
    fresh_observation = add_observation(
        session,
        subject.id,
        identifier_id=email.id,
        source="synthetic_fresh",
        source_locator="synthetic://fresh",
        observed_at=EVALUATED_AT - timedelta(days=1),
        source_mode=ObservationSourceMode.SYNTHETIC,
        normalized_payload={"email": "analyst@example.test"},
    )

    same_handle_result = create_correlation_run(
        session,
        subject_id=subject.id,
        candidate_identifier_id=username.id,
        factor_inputs=[
            {
                "factor_name": "same_username",
                "raw_weight": 10,
                "independence_group": "username_account",
                "observation_ids": [stale_observation.id],
                "contribution": 0,
                "stale": True,
            }
        ],
        contradiction_codes=[],
        outcome="insufficient_evidence",
        calibration_status=CalibrationStatus.UNCALIBRATED,
        is_identity_claim=False,
        evaluated_at=EVALUATED_AT,
    )
    exact_email_result = create_correlation_run(
        session,
        subject_id=subject.id,
        candidate_identifier_id=email.id,
        factor_inputs=[
            {
                "factor_name": "exact_public_email",
                "raw_weight": 70,
                "independence_group": "email_overlap",
                "observation_ids": [fresh_observation.id],
                "contribution": 70,
                "stale": False,
            }
        ],
        contradiction_codes=[],
        outcome="strong_evidence",
        calibration_status=CalibrationStatus.UNCALIBRATED,
        is_identity_claim=False,
        evaluated_at=EVALUATED_AT,
    )
    session.commit()

    case = {
        "engine": engine,
        "session": session,
        "subject": subject,
        "username": username,
        "email": email,
        "stale_observation": stale_observation,
        "fresh_observation": fresh_observation,
        "same_handle_result": same_handle_result,
        "exact_email_result": exact_email_result,
    }
    try:
        yield case
    finally:
        session.close()
        engine.dispose()


def test_dashboard_read_model_has_bounded_evidence_and_factor_sections(
    synthetic_case: dict[str, object],
) -> None:
    case = synthetic_case
    read_model = CaseReadModelService(case["session"]).build(
        case["subject"].id,
        at=EVALUATED_AT,
    )

    assert read_model.subject.id == case["subject"].id
    assert len(read_model.identifiers) == 2
    assert len(read_model.observations) == 2
    assert len(read_model.correlation_runs) == 2
    assert {run.calibration_status for run in read_model.correlation_runs} == {
        CalibrationStatus.UNCALIBRATED
    }
    assert all(run.is_identity_claim is False for run in read_model.correlation_runs)


def test_dashboard_read_model_marks_stale_observation_and_zero_contribution(
    synthetic_case: dict[str, object],
) -> None:
    case = synthetic_case
    read_model = CaseReadModelService(case["session"]).build(
        case["subject"].id,
        at=EVALUATED_AT,
    )

    stale = next(
        observation
        for observation in read_model.observations
        if observation.id == case["stale_observation"].id
    )
    assert stale.stale is True

    run = next(
        item
        for item in read_model.correlation_runs
        if item.run_id == case["same_handle_result"].run_id
    )
    factor = run.factors[0]
    assert factor.stale is True
    assert factor.contribution == 0


def test_dashboard_read_model_preserves_source_locator_and_provenance(
    synthetic_case: dict[str, object],
) -> None:
    case = synthetic_case
    read_model = CaseReadModelService(case["session"]).build(
        case["subject"].id,
        at=EVALUATED_AT,
    )

    fresh = next(
        observation
        for observation in read_model.observations
        if observation.id == case["fresh_observation"].id
    )
    assert fresh.source_locator == "synthetic://fresh"
    assert fresh.source == "synthetic_fresh"

    run = next(
        item
        for item in read_model.correlation_runs
        if item.run_id == case["exact_email_result"].run_id
    )
    assert run.factors[0].observation_ids == [case["fresh_observation"].id]


def test_dashboard_read_model_refuses_tampered_correlation_output(
    synthetic_case: dict[str, object],
) -> None:
    case = synthetic_case
    run = case["session"].get(
        CorrelationRun,
        case["same_handle_result"].run_id,
    )
    payload = json.loads(run.normalized_output)
    payload["outcome"] = "tampered"
    run.normalized_output = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    case["session"].flush()

    with pytest.raises(DashboardReadModelError, match="digest mismatch"):
        CaseReadModelService(case["session"]).build(
            case["subject"].id,
            at=EVALUATED_AT,
        )


def test_dashboard_read_model_refuses_tampered_identity_claim(
    synthetic_case: dict[str, object],
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
