# SPDX-License-Identifier: Apache-2.0
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_private_api_responses_are_not_cacheable() -> None:
    health = client.get("/health")
    assert health.status_code == 200
    assert health.headers["Cache-Control"] == "no-store"

    client.cookies.clear()
    denied = client.get("/v1/auth/session")
    assert denied.status_code == 401
    assert denied.headers["Cache-Control"] == "no-store"
