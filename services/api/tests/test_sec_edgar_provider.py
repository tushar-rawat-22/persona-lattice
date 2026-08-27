# SPDX-License-Identifier: Apache-2.0
from uuid import uuid4

import pytest

from app.models import Purpose
from app.providers.base import (
    ContactRisk,
    ProviderDescriptor,
    ProviderQuery,
    ProviderStatus,
    SourceCategory,
)
from app.providers.errors import (
    ProviderConfigurationError,
    ProviderResultValidationError,
    ProviderValidationError,
)
from app.providers.sec_edgar import SecEdgarExactCikProvider


CIK = "0000320193"
URL = "https://data.sec.gov/submissions/CIK0000320193.json"
USER_AGENT = "PersonaLattice ops@example.com"


def _descriptor() -> ProviderDescriptor:
    return ProviderDescriptor(
        name="sec_edgar_exact_cik",
        capability="public_company_filer_registry_metadata",
        status=ProviderStatus.DEVELOPMENT.value,
        contact_risk=ContactRisk.NONE_KNOWN,
        reason="Test descriptor for the bounded exact-CIK SEC provider.",
        version="test",
        source_category=SourceCategory.REGISTRY,
        allowed_purposes=frozenset({Purpose.PUBLIC_SOURCE_RESEARCH}),
        supported_identifier_kinds=frozenset({"url"}),
        max_attempts=1,
        timeout_seconds=4.0,
        max_response_bytes=256 * 1024,
        max_concurrency=1,
        rate_limit=6,
        rate_window_seconds=60.0,
    )


def _query(value: str = URL, *, kind: str = "url") -> ProviderQuery:
    return ProviderQuery(
        subject_id=uuid4(),
        identifier_id=uuid4(),
        identifier_kind=kind,
        identifier_value=value,
    )


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
                "accessionNumber": ["0000320193-26-000001"],
                "form": ["10-Q"],
                "filingDate": ["2026-01-30"],
            }
        },
    }


@pytest.mark.asyncio
async def test_exact_cik_provider_returns_bounded_registry_observation() -> None:
    calls: list[tuple[str, str]] = []

    async def fetcher(cik: str, *, user_agent: str) -> dict[str, object]:
        calls.append((cik, user_agent))
        return _payload()

    provider = SecEdgarExactCikProvider(
        descriptor=_descriptor(),
        fetcher=fetcher,
        user_agent_loader=lambda: USER_AGENT,
    )
    result = await provider.execute(_query(), None)

    assert calls == [(CIK, USER_AGENT)]
    assert len(result.observations) == 1
    observation = result.observations[0]
    assert observation.source_locator == URL
    assert observation.payload["sec_cik"] == CIK
    assert observation.payload["sec_filer_name"] == "Apple Inc."
    assert observation.payload["identity_claim"] is False
    assert observation.payload["registry_evidence"] is True
    assert "addresses" not in observation.payload
    assert "formerNames" not in observation.payload


@pytest.mark.asyncio
async def test_missing_operator_identity_stops_before_fetch() -> None:
    attempted = False

    async def fetcher(cik: str, *, user_agent: str) -> dict[str, object]:
        nonlocal attempted
        attempted = True
        return _payload()

    provider = SecEdgarExactCikProvider(
        descriptor=_descriptor(),
        fetcher=fetcher,
        user_agent_loader=lambda: None,
    )
    with pytest.raises(ProviderConfigurationError):
        await provider.execute(_query(), None)
    assert attempted is False


@pytest.mark.asyncio
async def test_sec_no_match_is_neutral_empty_result() -> None:
    async def fetcher(cik: str, *, user_agent: str) -> None:
        return None

    provider = SecEdgarExactCikProvider(
        descriptor=_descriptor(),
        fetcher=fetcher,
        user_agent_loader=lambda: USER_AGENT,
    )
    result = await provider.execute(_query(), None)
    assert result.observations == ()


@pytest.mark.asyncio
async def test_post_fetch_contract_violation_is_result_validation_failure() -> None:
    payload = _payload()
    payload["cik"] = 1

    async def fetcher(cik: str, *, user_agent: str) -> dict[str, object]:
        return payload

    provider = SecEdgarExactCikProvider(
        descriptor=_descriptor(),
        fetcher=fetcher,
        user_agent_loader=lambda: USER_AGENT,
    )
    with pytest.raises(ProviderResultValidationError):
        await provider.execute(_query(), None)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("kind", "value"),
    [
        ("username", "apple"),
        ("url", "https://www.sec.gov/edgar/browse/?CIK=320193"),
        ("url", "https://data.sec.gov/submissions/CIK0000320193.json?x=1"),
    ],
)
async def test_non_exact_inputs_fail_before_fetch(kind: str, value: str) -> None:
    attempted = False

    async def fetcher(cik: str, *, user_agent: str) -> dict[str, object]:
        nonlocal attempted
        attempted = True
        return _payload()

    provider = SecEdgarExactCikProvider(
        descriptor=_descriptor(),
        fetcher=fetcher,
        user_agent_loader=lambda: USER_AGENT,
    )
    with pytest.raises(ProviderValidationError):
        await provider.execute(_query(value, kind=kind), None)
    assert attempted is False


@pytest.mark.asyncio
async def test_credentials_are_rejected_before_fetch() -> None:
    provider = SecEdgarExactCikProvider(
        descriptor=_descriptor(),
        user_agent_loader=lambda: USER_AGENT,
    )
    with pytest.raises(ProviderValidationError):
        await provider.execute(_query(), "not-allowed")
