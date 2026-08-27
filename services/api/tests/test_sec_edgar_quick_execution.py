# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from uuid import uuid4

import pytest

from app.models import Purpose
from app.providers.errors import ProviderConfigurationError
from app.providers.sec_edgar_quick import execute_sec_edgar_exact_url
from app.providers.shared_runtime import DEFAULT_SEC_EDGAR_PROVIDER


SEC_URL = "https://data.sec.gov/submissions/CIK0000320193.json"


def _payload() -> dict[str, object]:
    return {
        "cik": 320193,
        "name": "Apple Inc.",
        "sic": "3571",
        "stateOfIncorporation": "CA",
        "fiscalYearEnd": "0927",
        "tickers": ["AAPL"],
        "exchanges": ["Nasdaq"],
        "filings": {
            "recent": {
                "accessionNumber": ["0000320193-26-000100"],
                "filingDate": ["2026-08-01"],
                "form": ["10-Q"],
            }
        },
    }


@pytest.mark.asyncio
async def test_exact_url_uses_process_owned_sec_adapter(monkeypatch) -> None:
    calls = 0

    async def fetcher(cik: str, *, user_agent: str) -> dict[str, object]:
        nonlocal calls
        calls += 1
        assert cik == "0000320193"
        assert user_agent == "PersonaLattice ops@example.com"
        return _payload()

    monkeypatch.setattr(DEFAULT_SEC_EDGAR_PROVIDER, "fetcher", fetcher)
    monkeypatch.setattr(
        DEFAULT_SEC_EDGAR_PROVIDER,
        "user_agent_loader",
        lambda: "PersonaLattice ops@example.com",
    )

    result = await execute_sec_edgar_exact_url(
        SEC_URL,
        subject_id=uuid4(),
        identifier_id=uuid4(),
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
    )

    assert result is not None
    assert calls == 1
    assert len(result.observations) == 1
    observation = result.observations[0]
    assert observation.source_locator == SEC_URL
    assert observation.payload["sec_cik"] == "0000320193"
    assert observation.payload["sec_filer_name"] == "Apple Inc."
    assert observation.payload["identity_claim"] is False


@pytest.mark.asyncio
async def test_non_sec_url_never_contacts_sec_adapter(monkeypatch) -> None:
    async def should_not_run(*args, **kwargs):
        raise AssertionError("non-SEC URLs must not consume SEC provider budget")

    monkeypatch.setattr(DEFAULT_SEC_EDGAR_PROVIDER, "fetcher", should_not_run)
    monkeypatch.setattr(
        DEFAULT_SEC_EDGAR_PROVIDER,
        "user_agent_loader",
        lambda: "PersonaLattice ops@example.com",
    )

    result = await execute_sec_edgar_exact_url(
        "https://example.com/public-page",
        subject_id=uuid4(),
        identifier_id=uuid4(),
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
    )

    assert result is None


@pytest.mark.asyncio
async def test_missing_operator_identity_fails_before_network_contact(monkeypatch) -> None:
    async def should_not_run(*args, **kwargs):
        raise AssertionError("missing SEC operator identity must fail before contact")

    monkeypatch.setattr(DEFAULT_SEC_EDGAR_PROVIDER, "fetcher", should_not_run)
    monkeypatch.setattr(DEFAULT_SEC_EDGAR_PROVIDER, "user_agent_loader", lambda: None)

    with pytest.raises(ProviderConfigurationError):
        await execute_sec_edgar_exact_url(
            SEC_URL,
            subject_id=uuid4(),
            identifier_id=uuid4(),
            purpose=Purpose.SELF_AUDIT,
            consent_acknowledged=True,
        )
