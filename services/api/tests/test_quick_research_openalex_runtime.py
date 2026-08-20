# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import pytest

from app.intelligence.source_states import SourceRunReason, SourceRunState
from app.models import Purpose
from app.providers.errors import ProviderResultValidationError, ProviderRemoteRateLimitError
from app.providers.shared_runtime import DEFAULT_OPENALEX_PROVIDER, DEFAULT_PROVIDER_RUNTIME
from app.research import ResearchKind, run_quick_research


async def _no_public_search(_value: str):
    return ()


async def _no_source(*args, **kwargs):
    return []


@pytest.mark.asyncio
async def test_exact_openalex_author_url_executes_shared_runtime(monkeypatch) -> None:
    async def fetcher(author_id: str, secret: str) -> dict[str, object]:
        assert author_id == "A5023888391"
        assert secret == "free-openalex-key"
        return {
            "id": "https://openalex.org/A5023888391",
            "display_name": "Example Scholar",
            "works_count": 17,
            "cited_by_count": 91,
            "orcid": "not retained",
        }

    monkeypatch.setattr(DEFAULT_PROVIDER_RUNTIME, "secret_resolver", lambda name: "free-openalex-key")
    monkeypatch.setattr(DEFAULT_OPENALEX_PROVIDER, "fetcher", fetcher)
    monkeypatch.setattr("app.research._dns_observations", _no_source)
    monkeypatch.setattr("app.research._wayback_observations", _no_source)

    report = await run_quick_research(
        kind=ResearchKind.URL,
        value="https://openalex.org/A5023888391",
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        public_search_lookup=_no_public_search,
    )

    observation = next(item for item in report.observations if item.source == "openalex_exact_author")
    assert observation.source_locator == "https://openalex.org/A5023888391"
    assert observation.details == {
        "openalex_author_id": "A5023888391",
        "openalex_display_name": "Example Scholar",
        "openalex_works_count": 17,
        "openalex_cited_by_count": 91,
        "data_license": "CC0",
        "api_attribution": "OpenAlex",
        "identity_claim": False,
    }

    source_run = next(item for item in report.source_runs if item.source_name == "openalex_exact_author")
    assert source_run.state is SourceRunState.EXECUTED
    assert source_run.observation_count == 1
    assert source_run.execution_attempted is True


@pytest.mark.asyncio
async def test_ordinary_url_does_not_attempt_openalex_provider(monkeypatch) -> None:
    async def should_not_run(author_id: str, secret: str) -> dict[str, object]:
        raise AssertionError("OpenAlex provider must not run for an ordinary URL")

    monkeypatch.setattr(DEFAULT_OPENALEX_PROVIDER, "fetcher", should_not_run)
    monkeypatch.setattr("app.research._dns_observations", _no_source)
    monkeypatch.setattr("app.research._wayback_observations", _no_source)

    report = await run_quick_research(
        kind=ResearchKind.URL,
        value="https://example.com/public-page",
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        public_search_lookup=_no_public_search,
    )

    assert all(item.source != "openalex_exact_author" for item in report.observations)
    assert all(item.source_name != "openalex_exact_author" for item in report.source_runs)


@pytest.mark.asyncio
async def test_missing_openalex_key_is_non_attempt_credential_state(monkeypatch) -> None:
    monkeypatch.setattr(DEFAULT_PROVIDER_RUNTIME, "secret_resolver", lambda name: None)
    monkeypatch.setattr("app.research._dns_observations", _no_source)
    monkeypatch.setattr("app.research._wayback_observations", _no_source)

    report = await run_quick_research(
        kind=ResearchKind.URL,
        value="https://openalex.org/A5023888391",
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        public_search_lookup=_no_public_search,
    )

    source_run = next(item for item in report.source_runs if item.source_name == "openalex_exact_author")
    assert source_run.state is SourceRunState.UNAVAILABLE
    assert source_run.reason is SourceRunReason.CREDENTIAL_NOT_CONFIGURED
    assert source_run.execution_attempted is False
    assert "OpenAlex exact-author metadata was temporarily unavailable." not in report.warnings


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("exc", "expected_reason"),
    [
        (ProviderRemoteRateLimitError("remote limit", retry_after=3.0), SourceRunReason.REMOTE_RATE_LIMIT),
        (ProviderResultValidationError("bad returned author"), SourceRunReason.MALFORMED_RESULT),
    ],
)
async def test_openalex_runtime_preserves_attempted_failure_phase(
    monkeypatch,
    exc,
    expected_reason,
) -> None:
    async def fail(*args, **kwargs):
        raise exc

    monkeypatch.setattr("app.research._openalex_observations", fail)
    monkeypatch.setattr("app.research._dns_observations", _no_source)
    monkeypatch.setattr("app.research._wayback_observations", _no_source)

    report = await run_quick_research(
        kind=ResearchKind.URL,
        value="https://openalex.org/A5023888391",
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        public_search_lookup=_no_public_search,
    )

    source_run = next(item for item in report.source_runs if item.source_name == "openalex_exact_author")
    assert source_run.state is SourceRunState.UNAVAILABLE
    assert source_run.reason is expected_reason
    assert source_run.execution_attempted is True
    assert "OpenAlex exact-author metadata was temporarily unavailable." in report.warnings
