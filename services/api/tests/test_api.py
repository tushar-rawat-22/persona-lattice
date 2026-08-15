# SPDX-License-Identifier: Apache-2.0
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_preview_normalizes_intake() -> None:
    response = client.post(
        "/v1/intake/preview",
        json={
            "purpose": "self_audit",
            "consent_acknowledged": True,
            "phones": ["+91 98765 43210"],
            "emails": [" Test@Example.com "],
            "usernames": ["@demo_user"],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "planned_only"
    assert body["normalized"]["emails"] == ["test@example.com"]
    assert body["normalized"]["usernames"] == ["demo_user"]


def test_regulated_decision_is_blocked() -> None:
    response = client.post(
        "/v1/intake/preview",
        json={
            "purpose": "employment_decision",
            "consent_acknowledged": True,
            "full_name": "Synthetic Person",
        },
    )
    assert response.status_code == 422


def test_consent_is_required_for_self_audit() -> None:
    response = client.post(
        "/v1/intake/preview",
        json={
            "purpose": "self_audit",
            "consent_acknowledged": False,
            "full_name": "Synthetic Person",
        },
    )
    assert response.status_code == 422
