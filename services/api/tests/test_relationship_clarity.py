# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
import json
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.admin_auth import LOGIN_THROTTLE, SESSION_STORE, hash_admin_password
from app.cases import CASE_STORE, StoredCase
from app.main import app
from app.relationship_clarity import (
    RelationshipClarityProjectionError,
    build_relationship_clarity_projection,
)
from app.research import ResearchKind


client = TestClient(app)
PASSWORD = "synthetic-admin-password-123!"
CASE_ID = UUID("00000000-0000-4000-8000-000000000252")
CREATED_AT = datetime(2026, 9, 30, 12, 0, tzinfo=UTC)


def _source_run(source: str, *, state: str = "executed", reason: str = "results_returned"):
    return {
        "source": source,
        "lead_kind": "username",
        "state": state,
        "reason": reason,
        "observation_count": 1 if state == "executed" else 0,
        "execution_attempted": state in {"executed", "not_found", "withheld", "unavailable"},
        "terminal": True,
    }


def _retained_report() -> dict[str, object]:
    seed_key = "email:known@example.test"
    candidate_key = "username:public-user"
    return {
        "kind": "email",
        "normalized_value": "known@example.test",
        "converged_report": {
            "report_version": "private-converged-evidence-report-v1",
            "seed": {"kind": "email", "normalized_value": "known@example.test"},
            "nodes": [
                {
                    "key": seed_key,
                    "kind": "email",
                    "normalized_value": "known@example.test",
                    "depth": 0,
                    "parent_key": None,
                    "pivot_reason": "seed",
                    "warnings": [],
                    "source_runs": {"records": []},
                    "observations": [],
                },
                {
                    "key": candidate_key,
                    "kind": "username",
                    "normalized_value": "public-user",
                    "depth": 1,
                    "parent_key": seed_key,
                    "pivot_reason": "public_username",
                    "warnings": [],
                    "source_runs": {
                        "records": [
                            _source_run("github_public_api"),
                            _source_run("synthetic_contradiction"),
                            _source_run(
                                "provider_without_observation",
                                state="not_found",
                                reason="no_match",
                            ),
                            _source_run(
                                "failed_provider",
                                state="unavailable",
                                reason="execution_failure",
                            ),
                        ]
                    },
                    "observations": [
                        {
                            "source": "github_public_api",
                            "source_locator": "https://github.com/public-user",
                            "summary": "The original email seed is explicitly public.",
                            "details": {
                                "account_candidate": True,
                                "identity_claim": False,
                                "public_email": "known@example.test",
                            },
                        },
                        {
                            "source": "synthetic_contradiction",
                            "source_locator": "https://evidence.example.test/conflict",
                            "summary": "Public ownership evidence conflicts with the candidate.",
                            "details": {"identity_claim": False},
                        },
                    ],
                },
            ],
            "edges": [],
            "lead_graph": {"decisions": []},
            "m5": {
                "engine": "m5-deterministic-evidence-strength",
                "evaluated_at": "2026-09-30T12:01:00+00:00",
                "calibration_status": "uncalibrated",
                "is_identity_claim": False,
                "evaluations": [
                    {
                        "candidate_node": candidate_key,
                        "candidate_observation_index": 0,
                        "outcome": "contradicted",
                        "calibration_status": "uncalibrated",
                        "is_identity_claim": False,
                        "factors": [
                            {
                                "kind": "exact_confirmed_identifier_overlap",
                                "status": "applied",
                                "rationale": "Exact retained identifier overlap.",
                                "veto": False,
                                "observation_refs": [
                                    {"node_key": candidate_key, "observation_index": 0}
                                ],
                                "identifier_refs": [seed_key],
                            },
                            {
                                "kind": "compatible_profile_metadata",
                                "status": "applied_unknown_freshness",
                                "rationale": "Compatible public profile metadata needs review.",
                                "veto": False,
                                "observation_refs": [
                                    {"node_key": candidate_key, "observation_index": 0}
                                ],
                                "identifier_refs": [],
                            },
                            {
                                "kind": "hard_contradiction",
                                "status": "applied",
                                "rationale": "Explicit retained ownership contradiction.",
                                "veto": True,
                                "observation_refs": [
                                    {"node_key": candidate_key, "observation_index": 1}
                                ],
                                "identifier_refs": [],
                            },
                        ],
                    }
                ],
            },
        },
    }


def _record(report: dict[str, object] | None = None) -> StoredCase:
    return StoredCase(
        id=CASE_ID,
        created_at=CREATED_AT,
        expires_at=datetime(2026, 10, 30, 12, 0, tzinfo=UTC),
        seed_kind=ResearchKind.EMAIL,
        seed_value="known@example.test",
        report=report or _retained_report(),
    )


def _configure(monkeypatch, tmp_path) -> None:
    client.cookies.clear()
    SESSION_STORE.clear()
    LOGIN_THROTTLE.clear()
    monkeypatch.setenv("PERSONALATTICE_ADMIN_USERNAME", "admin")
    monkeypatch.setenv("PERSONALATTICE_ADMIN_PASSWORD_HASH", hash_admin_password(PASSWORD))
    monkeypatch.setenv("PERSONALATTICE_COOKIE_SECURE", "false")
    monkeypatch.setenv("PERSONALATTICE_SESSION_COOKIE", "personalattice_test_session")
    monkeypatch.setenv("PERSONALATTICE_DB_PATH", str(tmp_path / "cases.sqlite3"))


def _login() -> None:
    response = client.post(
        "/v1/auth/login",
        json={"username": "admin", "password": PASSWORD},
    )
    assert response.status_code == 200, response.text


def test_projection_is_deterministic_typed_and_non_probabilistic() -> None:
    first = build_relationship_clarity_projection(_record())
    second = build_relationship_clarity_projection(_record())

    assert first == second
    payload = first.model_dump(mode="json")
    assert payload["version"] == "relationship-clarity-projection-v1"
    assert payload["relationship_states"] == [
        "corroborated",
        "unresolved",
        "contradiction",
    ]
    assert payload["deterministic"] is True
    assert payload["probabilistic"] is False
    assert {node["kind"] for node in payload["nodes"]} == {"identifier", "observation"}
    assert {edge["state"] for edge in payload["edges"]} == {
        "corroborated",
        "unresolved",
        "contradiction",
    }
    assert all(edge["provenance"] for edge in payload["edges"])
    assert all(item["source_state"] == "executed" for edge in payload["edges"] for item in edge["provenance"])
    assert {edge["relationship_reason"] for edge in payload["edges"]} == {
        "Exact retained identifier overlap.",
        "Compatible public profile metadata needs review.",
        "Explicit retained ownership contradiction.",
    }

    serialized = json.dumps(payload, sort_keys=True)
    for forbidden in ("evidence_score", "identity_probability", "confidence", "percentage"):
        assert forbidden not in serialized
    assert "provider_without_observation" not in serialized
    assert "failed_provider" not in serialized


def test_projection_fails_closed_without_canonical_factor_references() -> None:
    report = _retained_report()
    del report["converged_report"]["m5"]["evaluations"][0]["factors"][0][
        "observation_refs"
    ]

    with pytest.raises(
        RelationshipClarityProjectionError,
        match="canonical observation_refs",
    ):
        build_relationship_clarity_projection(_record(report))


def test_projection_fails_closed_when_provenance_source_state_is_not_retained() -> None:
    report = _retained_report()
    report["converged_report"]["nodes"][1]["source_runs"]["records"] = []

    with pytest.raises(RelationshipClarityProjectionError, match="source-run state"):
        build_relationship_clarity_projection(_record(report))


def test_projection_endpoint_is_authenticated_read_only_and_no_store(monkeypatch, tmp_path) -> None:
    _configure(monkeypatch, tmp_path)
    created = CASE_STORE.create_payload(
        seed_kind=ResearchKind.EMAIL,
        seed_value="known@example.test",
        report_payload=deepcopy(_retained_report()),
        now=CREATED_AT,
    )
    before = deepcopy(CASE_STORE.get(created.id).report)

    assert client.get(f"/v1/cases/{created.id}/relationship-clarity").status_code == 401
    _login()
    response = client.get(f"/v1/cases/{created.id}/relationship-clarity")

    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    assert response.json()["case_id"] == str(created.id)
    assert CASE_STORE.get(created.id).report == before


def test_projection_endpoint_rejects_historical_payload_without_reference_hydration(
    monkeypatch,
    tmp_path,
) -> None:
    _configure(monkeypatch, tmp_path)
    report = _retained_report()
    del report["converged_report"]["m5"]["evaluations"][0]["factors"][0][
        "identifier_refs"
    ]
    created = CASE_STORE.create_payload(
        seed_kind=ResearchKind.EMAIL,
        seed_value="known@example.test",
        report_payload=report,
        now=CREATED_AT,
    )
    _login()

    response = client.get(f"/v1/cases/{created.id}/relationship-clarity")

    assert response.status_code == 409
    assert response.headers["cache-control"] == "no-store"
    assert response.json() == {
        "detail": "Relationship clarity is unavailable because retained evidence references are incomplete."
    }
