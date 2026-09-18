import logging
import re

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.main import app as production_app
from app.operational_access_logging import LOGGER_NAME, install_operational_access_logging


PRIVATE_QUERY = "synthetic-private-search-term"
PRIVATE_CASE_A = "11111111-1111-4111-8111-111111111111"
PRIVATE_CASE_B = "22222222-2222-4222-8222-222222222222"
PRIVATE_CREDENTIALS = {
    "authorization": "Bearer synthetic-session-token",
    "cookie": "__Host-personalattice=synthetic-cookie",
    "x-personalattice-csrf": "synthetic-csrf-token",
    "x-provider-key": "synthetic-provider-key",
}


def _test_app() -> FastAPI:
    app = FastAPI()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/v1/auth/session")
    def session_denial() -> dict[str, str]:
        from fastapi import HTTPException

        raise HTTPException(status_code=401, detail="denied")

    @app.get("/v1/cases")
    def case_search(q: str | None = None) -> dict[str, bool]:
        return {"matched": bool(q)}

    @app.get("/v1/cases/{case_id}")
    def case_detail(case_id: str) -> dict[str, str]:
        return {"case_id": case_id}

    @app.get("/v1/cases/{case_id}/decisions")
    def case_decisions(case_id: str) -> dict[str, str]:
        return {"case_id": case_id}

    @app.post("/v1/uploads/review")
    async def upload_review(request: Request) -> dict[str, int]:
        return {"bytes": len(await request.body())}

    @app.get("/v1/diagnostic-failure")
    def diagnostic_failure() -> None:
        raise RuntimeError("synthetic operational failure")

    install_operational_access_logging(app)
    return app


def _messages(caplog) -> list[str]:
    return [record.getMessage() for record in caplog.records if record.name == LOGGER_NAME]


def test_operational_logs_keep_route_status_and_timing_without_private_values(caplog) -> None:
    client = TestClient(_test_app(), raise_server_exceptions=False)

    with caplog.at_level(logging.INFO, logger=LOGGER_NAME):
        assert client.get("/health").status_code == 200
        assert client.get("/v1/auth/session").status_code == 401
        assert client.get(f"/v1/cases?q={PRIVATE_QUERY}").status_code == 200
        first = client.get(f"/v1/cases/{PRIVATE_CASE_A}")
        second = client.get(f"/v1/cases/{PRIVATE_CASE_B}")
        assert first.json()["case_id"] == PRIVATE_CASE_A
        assert second.json()["case_id"] == PRIVATE_CASE_B
        assert client.get(f"/v1/cases/{PRIVATE_CASE_A}/decisions").status_code == 200
        assert client.get(f"/missing/{PRIVATE_QUERY}").status_code == 404
        assert client.get("/v1/diagnostic-failure").status_code == 500

    messages = _messages(caplog)
    combined = "\n".join(messages)

    for private_value in (PRIVATE_QUERY, PRIVATE_CASE_A, PRIVATE_CASE_B):
        assert private_value not in combined

    assert "method=GET route=/health status=200" in combined
    assert "method=GET route=/v1/auth/session status=401" in combined
    assert "method=GET route=/v1/cases status=200" in combined
    assert combined.count("method=GET route=/v1/cases/{case_id} status=200") == 2
    assert "method=GET route=/v1/cases/{case_id}/decisions status=200" in combined
    assert "method=GET route=unmatched status=404" in combined
    assert "method=GET route=/v1/diagnostic-failure status=500" in combined
    assert all(re.search(r" duration_ms=\d+(?:\.\d+)?$", message) for message in messages)


def test_operational_logs_ignore_headers_cookies_and_request_bodies(caplog) -> None:
    client = TestClient(_test_app())
    raw_upload = b"synthetic raw upload content"

    with caplog.at_level(logging.INFO, logger=LOGGER_NAME):
        response = client.post(
            "/v1/uploads/review?provider_key=synthetic-query-secret",
            headers=PRIVATE_CREDENTIALS,
            content=raw_upload,
        )

    assert response.status_code == 200
    combined = "\n".join(_messages(caplog))
    assert "method=POST route=/v1/uploads/review status=200" in combined
    for private_value in (*PRIVATE_CREDENTIALS.values(), raw_upload.decode(), "synthetic-query-secret"):
        assert private_value not in combined


def test_production_app_registers_metadata_safe_operational_logging(caplog) -> None:
    client = TestClient(production_app)

    with caplog.at_level(logging.INFO, logger=LOGGER_NAME):
        assert client.get("/health").status_code == 200
        session = client.get("/v1/auth/session")
        cases = client.get(f"/v1/cases?q={PRIVATE_QUERY}")

    assert session.status_code in {401, 503}
    assert cases.status_code in {401, 503}

    combined = "\n".join(_messages(caplog))
    assert PRIVATE_QUERY not in combined
    assert "method=GET route=/health status=200" in combined
    assert f"method=GET route=/v1/auth/session status={session.status_code}" in combined
    assert f"method=GET route=/v1/cases status={cases.status_code}" in combined
