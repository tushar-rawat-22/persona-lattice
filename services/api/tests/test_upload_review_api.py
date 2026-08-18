# SPDX-License-Identifier: Apache-2.0
from pathlib import Path
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.admin_auth import LOGIN_THROTTLE, SESSION_STORE, hash_admin_password
from app.audit import AUDIT_STORE
from app.cases import CASE_STORE
from app.main import app
from app.models import Purpose
from app.research import QuickResearchReport, ResearchKind
from app.uploads import research_service


client = TestClient(app)
PASSWORD = "synthetic-admin-password-123!"


def _configure_and_login(monkeypatch, tmp_path: Path) -> str:
    client.cookies.clear()
    SESSION_STORE.clear()
    LOGIN_THROTTLE.clear()
    monkeypatch.setenv("PERSONALATTICE_ADMIN_USERNAME", "admin")
    monkeypatch.setenv("PERSONALATTICE_ADMIN_PASSWORD_HASH", hash_admin_password(PASSWORD))
    monkeypatch.setenv("PERSONALATTICE_COOKIE_SECURE", "false")
    monkeypatch.setenv("PERSONALATTICE_SESSION_COOKIE", "personalattice_review_test_session")
    monkeypatch.setenv("PERSONALATTICE_DB_PATH", str(tmp_path / "state.db"))
    monkeypatch.setenv("PERSONALATTICE_UPLOAD_DIR", str(tmp_path / "uploads"))
    response = client.post(
        "/v1/auth/login",
        json={"username": "admin", "password": PASSWORD},
    )
    assert response.status_code == 200, response.text
    return response.json()["csrf_token"]


def _headers(csrf: str) -> dict[str, str]:
    return {"X-PersonaLattice-CSRF": csrf}


def _preview_email_candidate(csrf: str) -> tuple[str, str, str]:
    response = client.post(
        "/v1/files/preview",
        headers=_headers(csrf),
        data={"purpose": "self_audit", "consent_acknowledged": "true"},
        files=[
            (
                "files",
                (
                    "synthetic.txt",
                    b"Contact analyst@example.test for the public profile.",
                    "text/plain",
                ),
            )
        ],
    )
    assert response.status_code == 200, response.text
    artifact = response.json()["artifacts"][0]
    candidate = next(
        item for item in artifact["candidates"] if item["identifier_kind"] == "email"
    )
    return artifact["artifact_id"], candidate["candidate_id"], candidate["value"]


def _route(artifact_id: str, candidate_id: str, action: str) -> str:
    return f"/v1/files/review/{artifact_id}/{candidate_id}/{action}"


def test_upload_review_routes_require_admin_session(monkeypatch, tmp_path: Path) -> None:
    client.cookies.clear()
    SESSION_STORE.clear()
    monkeypatch.setenv("PERSONALATTICE_ADMIN_USERNAME", "admin")
    monkeypatch.setenv("PERSONALATTICE_ADMIN_PASSWORD_HASH", hash_admin_password(PASSWORD))
    monkeypatch.setenv("PERSONALATTICE_COOKIE_SECURE", "false")
    monkeypatch.setenv("PERSONALATTICE_SESSION_COOKIE", "personalattice_review_test_session")
    monkeypatch.setenv("PERSONALATTICE_DB_PATH", str(tmp_path / "state.db"))

    response = client.post(_route(str(uuid4()), str(uuid4()), "confirm"))

    assert response.status_code == 401


def test_upload_review_routes_require_csrf_after_login(monkeypatch, tmp_path: Path) -> None:
    _configure_and_login(monkeypatch, tmp_path)

    response = client.post(_route(str(uuid4()), str(uuid4()), "confirm"))

    assert response.status_code == 403
    assert response.json()["detail"] == "CSRF validation failed."


def test_upload_review_confirm_promote_reopen_and_reject_flow(monkeypatch, tmp_path: Path) -> None:
    csrf = _configure_and_login(monkeypatch, tmp_path)
    artifact_id, candidate_id, candidate_value = _preview_email_candidate(csrf)

    before_review = client.post(
        _route(artifact_id, candidate_id, "promote"),
        headers=_headers(csrf),
    )
    assert before_review.status_code == 409

    confirmed = client.post(
        _route(artifact_id, candidate_id, "confirm"),
        headers=_headers(csrf),
    )
    assert confirmed.status_code == 200, confirmed.text
    confirmed_body = confirmed.json()
    assert confirmed_body["artifact_id"] == artifact_id
    assert confirmed_body["candidate_id"] == candidate_id
    assert confirmed_body["candidate_type"] == "identifier"
    assert confirmed_body["identifier_kind"] == "email"
    assert confirmed_body["review_status"] == "confirmed"
    assert confirmed_body["external_research_authorized"] is True
    assert "value" not in confirmed_body

    promoted = client.post(
        _route(artifact_id, candidate_id, "promote"),
        headers=_headers(csrf),
    )
    assert promoted.status_code == 200, promoted.text
    promoted_body = promoted.json()
    assert promoted_body["kind"] == "email"
    assert promoted_body["value"] == candidate_value
    assert promoted_body["reason"] == "reviewed_document_identifier"
    assert promoted_body["disposition"] == "auto_pivot"
    assert artifact_id in promoted_body["source_locator"]
    assert candidate_id in promoted_body["source_locator"]

    reopened = client.post(
        _route(artifact_id, candidate_id, "reopen"),
        headers=_headers(csrf),
    )
    assert reopened.status_code == 200, reopened.text
    assert reopened.json()["review_status"] == "pending_human_review"
    assert reopened.json()["external_research_authorized"] is False

    after_reopen = client.post(
        _route(artifact_id, candidate_id, "promote"),
        headers=_headers(csrf),
    )
    assert after_reopen.status_code == 409

    rejected = client.post(
        _route(artifact_id, candidate_id, "reject"),
        headers=_headers(csrf),
    )
    assert rejected.status_code == 200, rejected.text
    assert rejected.json()["review_status"] == "rejected"
    assert rejected.json()["external_research_authorized"] is False


def test_reviewed_candidate_case_requires_current_authorization_and_preserves_provenance(
    monkeypatch,
    tmp_path: Path,
) -> None:
    csrf = _configure_and_login(monkeypatch, tmp_path)
    artifact_id, candidate_id, candidate_value = _preview_email_candidate(csrf)
    calls: list[dict[str, object]] = []

    async def fake_quick_research(**kwargs):
        calls.append(kwargs)
        return QuickResearchReport(
            kind=ResearchKind.EMAIL,
            normalized_value=str(kwargs["value"]),
            observations=(),
        )

    monkeypatch.setattr(research_service, "run_quick_research", fake_quick_research)
    body = {
        "mode": "quick",
        "purpose": "self_audit",
        "consent_acknowledged": True,
    }

    before_confirm = client.post(
        _route(artifact_id, candidate_id, "run-case"),
        headers=_headers(csrf),
        json=body,
    )
    assert before_confirm.status_code == 409
    assert calls == []

    confirmed = client.post(
        _route(artifact_id, candidate_id, "confirm"),
        headers=_headers(csrf),
    )
    assert confirmed.status_code == 200

    executed = client.post(
        _route(artifact_id, candidate_id, "run-case"),
        headers=_headers(csrf),
        json=body,
    )
    assert executed.status_code == 200, executed.text
    response_body = executed.json()
    assert response_body["mode"] == "quick"
    assert response_body["seed_kind"] == "email"
    assert "value" not in response_body
    assert len(calls) == 1
    assert calls[0]["kind"] is ResearchKind.EMAIL
    assert calls[0]["value"] == candidate_value
    assert calls[0]["purpose"] is Purpose.SELF_AUDIT
    assert calls[0]["consent_acknowledged"] is True

    record = CASE_STORE.get(UUID(response_body["case_id"]))
    assert record is not None
    provenance = record.report["seed_provenance"]
    assert provenance["source"] == "reviewed_upload_candidate"
    assert provenance["review_required"] is True
    assert artifact_id in provenance["source_locator"]
    assert candidate_id in provenance["source_locator"]

    reopened = client.post(
        _route(artifact_id, candidate_id, "reopen"),
        headers=_headers(csrf),
    )
    assert reopened.status_code == 200
    after_reopen = client.post(
        _route(artifact_id, candidate_id, "run-case"),
        headers=_headers(csrf),
        json=body,
    )
    assert after_reopen.status_code == 409
    assert len(calls) == 1


def test_reviewed_candidate_case_rechecks_purpose_before_provider_execution(
    monkeypatch,
    tmp_path: Path,
) -> None:
    csrf = _configure_and_login(monkeypatch, tmp_path)
    artifact_id, candidate_id, _candidate_value = _preview_email_candidate(csrf)
    confirmed = client.post(
        _route(artifact_id, candidate_id, "confirm"),
        headers=_headers(csrf),
    )
    assert confirmed.status_code == 200

    called = False

    async def fake_quick_research(**_kwargs):
        nonlocal called
        called = True
        raise AssertionError("provider runner must not execute before purpose enforcement")

    monkeypatch.setattr(research_service, "run_quick_research", fake_quick_research)
    response = client.post(
        _route(artifact_id, candidate_id, "run-case"),
        headers=_headers(csrf),
        json={
            "mode": "quick",
            "purpose": "self_audit",
            "consent_acknowledged": False,
        },
    )

    assert response.status_code == 422
    assert called is False


def test_upload_review_route_fails_closed_on_artifact_candidate_mismatch(
    monkeypatch,
    tmp_path: Path,
) -> None:
    csrf = _configure_and_login(monkeypatch, tmp_path)
    _artifact_id, candidate_id, _candidate_value = _preview_email_candidate(csrf)

    response = client.post(
        _route(str(uuid4()), candidate_id, "confirm"),
        headers=_headers(csrf),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Upload review candidate was not found or has expired."


def test_upload_review_audit_events_do_not_copy_identifier_values_or_ids(
    monkeypatch,
    tmp_path: Path,
) -> None:
    csrf = _configure_and_login(monkeypatch, tmp_path)
    artifact_id, candidate_id, candidate_value = _preview_email_candidate(csrf)

    confirm = client.post(
        _route(artifact_id, candidate_id, "confirm"),
        headers=_headers(csrf),
    )
    assert confirm.status_code == 200, confirm.text
    promote = client.post(
        _route(artifact_id, candidate_id, "promote"),
        headers=_headers(csrf),
    )
    assert promote.status_code == 200, promote.text

    events = [
        event
        for event in AUDIT_STORE.list_recent(limit=20)
        if event.event_type.startswith("file.review.")
    ]
    assert {event.event_type for event in events} >= {
        "file.review.confirm",
        "file.review.promote",
    }
    serialized = "\n".join(str(event.details) for event in events)
    assert candidate_value not in serialized
    assert artifact_id not in serialized
    assert candidate_id not in serialized
