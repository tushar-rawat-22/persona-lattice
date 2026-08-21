# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import pytest

from app.intelligence.source_states import SourceRunReason, SourceRunState
from app.models import Purpose
from app.providers.errors import ProviderResultValidationError, ProviderRemoteRateLimitError
from app.providers.shared_runtime import DEFAULT_CROSSREF_PROVIDER
from app.research import ResearchKind, run_quick_research


async def _no_public_search(_value: str):
    return ()


async def _no_source(*args, **kwargs):
    return []


@pytest.mark.asyncio
async def test_exact_doi_url_executes_crossref_through_shared_runtime(monkeypatch) -> None:
    async def fetcher(doi: str) -> dict[str, object]:
        assert doi == "10.1038/s41586-020-2649-2"
        return {
            "status": "ok",
            "message-type": "work",
            "message-version": "1.0.0",
            "message": {
                "DOI": "10.1038/s41586-020-2649-2",
                "title": ["A bounded publication title"],
                "published": {"date-parts": [[2020, 9, 3]]},
                "author": [{"given": "Ada", "family": "Example", "ORCID": "not retained"}],
                "abstract": "not retained",
            },
        }

    monkeypatch.setattr(DEFAULT_CROSSREF_PROVIDER, "fetcher", fetcher)
    monkeypatch.setattr("app.research._dns_observations", _no_source)
    monkeypatch.setattr("app.research._wayback_observations", _no_source)

    report = await run_quick_research(
        kind=ResearchKind.URL,
        value="https://doi.org/10.1038/s41586-020-2649-2",
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        public_search_lookup=_no_public_search,
    )

    observation = next(item for item in report.observations if item.source == "crossref_exact_work")
    assert observation.source_locator == "https://doi.org/10.1038/s41586-020-2649-2"
    assert observation.details == {
        "crossref_doi": "10.1038/s41586-020-2649-2",
        "crossref_title": "A bounded publication title",
        "crossref_author_names": ["Ada Example"],
        "author_names_display_only": True,
        "api_attribution": "Crossref",
        "identity_claim": False,
        "crossref_publication_year": 2020,
    }

    source_run = next(item for item in report.source_runs if item.source_name == "crossref_exact_work")
    assert source_run.state is SourceRunState.EXECUTED
    assert source_run.observation_count == 1
    assert source_run.execution_attempted is True


@pytest.mark.asyncio
async def test_ordinary_url_does_not_attempt_crossref(monkeypatch) -> None:
    async def should_not_run(doi: str) -> dict[str, object]:
        raise AssertionError("Crossref must not run for an ordinary URL")

    monkeypatch.setattr(DEFAULT_CROSSREF_PROVIDER, "fetcher", should_not_run)
    monkeypatch.setattr("app.research._dns_observations", _no_source)
    monkeypatch.setattr("app.research._wayback_observations", _no_source)

    report = await run_quick_research(
        kind=ResearchKind.URL,
        value="https://example.com/public-page",
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        public_search_lookup=_no_public_search,
    )

    assert all(item.source != "crossref_exact_work" for item in report.observations)
    assert all(item.source_name != "crossref_exact_work" for item in report.source_runs)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("exc", "expected_reason"),
    [
        (ProviderRemoteRateLimitError("remote limit", retry_after=3.0), SourceRunReason.REMOTE_RATE_LIMIT),
        (ProviderResultValidationError("bad returned DOI"), SourceRunReason.MALFORMED_RESULT),
    ],
)
async def test_crossref_runtime_preserves_attempted_failure_phase(monkeypatch, exc, expected_reason) -> None:
    async def fail(*args, **kwargs):
        raise exc

    monkeypatch.setattr("app.research._crossref_observations", fail)
    monkeypatch.setattr("app.research._dns_observations", _no_source)
    monkeypatch.setattr("app.research._wayback_observations", _no_source)

    report = await run_quick_research(
        kind=ResearchKind.URL,
        value="https://doi.org/10.1038/s41586-020-2649-2",
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        public_search_lookup=_no_public_search,
    )

    source_run = next(item for item in report.source_runs if item.source_name == "crossref_exact_work")
    assert source_run.state is SourceRunState.UNAVAILABLE
    assert source_run.reason is expected_reason
    assert source_run.execution_attempted is True
    assert "Crossref exact-work metadata was temporarily unavailable." in report.warnings
