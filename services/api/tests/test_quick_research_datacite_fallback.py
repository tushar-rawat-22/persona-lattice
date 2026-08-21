# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import pytest

from app.intelligence.source_states import SourceRunReason, SourceRunState
from app.models import Purpose
from app.providers.errors import ProviderRemoteRateLimitError
from app.providers.shared_runtime import DEFAULT_CROSSREF_PROVIDER, DEFAULT_DATACITE_PROVIDER
from app.research import ResearchKind, run_quick_research


async def _no_public_search(_value: str):
    return ()


async def _no_source(*args, **kwargs):
    return []


@pytest.fixture(autouse=True)
def _disable_unrelated_url_sources(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("app.research._dns_observations", _no_source)
    monkeypatch.setattr("app.research._wayback_observations", _no_source)


def _crossref_payload() -> dict[str, object]:
    return {
        "status": "ok",
        "message-type": "work",
        "message-version": "1.0.0",
        "message": {
            "DOI": "10.5438/0012",
            "title": ["Crossref owns this DOI"],
        },
    }


def _datacite_payload() -> dict[str, object]:
    return {
        "data": {
            "id": "10.5438/0012",
            "type": "dois",
            "attributes": {
                "doi": "10.5438/0012",
                "state": "findable",
                "titles": [{"title": "DataCite fallback record"}],
                "publicationYear": 2025,
                "types": {"resourceTypeGeneral": "Dataset"},
                "creators": [{"name": "Example, Ada", "nameIdentifiers": [{"nameIdentifier": "not retained"}]}],
            },
        }
    }


@pytest.mark.asyncio
async def test_crossref_success_prevents_datacite_attempt(monkeypatch: pytest.MonkeyPatch) -> None:
    async def crossref_fetcher(doi: str):
        assert doi == "10.5438/0012"
        return _crossref_payload()

    async def datacite_should_not_run(doi: str):
        raise AssertionError("DataCite must not run after Crossref success")

    monkeypatch.setattr(DEFAULT_CROSSREF_PROVIDER, "fetcher", crossref_fetcher)
    monkeypatch.setattr(DEFAULT_DATACITE_PROVIDER, "fetcher", datacite_should_not_run)

    report = await run_quick_research(
        kind=ResearchKind.URL,
        value="https://doi.org/10.5438/0012",
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        public_search_lookup=_no_public_search,
    )

    assert any(item.source == "crossref_exact_work" for item in report.observations)
    assert all(item.source != "datacite_exact_doi" for item in report.observations)
    assert all(item.source_name != "datacite_exact_doi" for item in report.source_runs)


@pytest.mark.asyncio
async def test_crossref_clean_no_match_unlocks_datacite(monkeypatch: pytest.MonkeyPatch) -> None:
    async def crossref_missing(doi: str):
        return None

    async def datacite_found(doi: str):
        assert doi == "10.5438/0012"
        return _datacite_payload()

    monkeypatch.setattr(DEFAULT_CROSSREF_PROVIDER, "fetcher", crossref_missing)
    monkeypatch.setattr(DEFAULT_DATACITE_PROVIDER, "fetcher", datacite_found)

    report = await run_quick_research(
        kind=ResearchKind.URL,
        value="https://doi.org/10.5438/0012",
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        public_search_lookup=_no_public_search,
    )

    crossref_run = next(item for item in report.source_runs if item.source_name == "crossref_exact_work")
    datacite_run = next(item for item in report.source_runs if item.source_name == "datacite_exact_doi")
    assert crossref_run.state is SourceRunState.EXECUTED
    assert crossref_run.observation_count == 0
    assert datacite_run.state is SourceRunState.EXECUTED
    assert datacite_run.observation_count == 1
    observation = next(item for item in report.observations if item.source == "datacite_exact_doi")
    assert observation.details == {
        "datacite_doi": "10.5438/0012",
        "datacite_title": "DataCite fallback record",
        "datacite_creator_names": ["Example, Ada"],
        "creator_names_display_only": True,
        "data_license": "CC0",
        "api_attribution": "DataCite",
        "identity_claim": False,
        "datacite_publication_year": 2025,
        "datacite_resource_type": "Dataset",
    }


@pytest.mark.asyncio
async def test_crossref_attempted_failure_does_not_fall_through(monkeypatch: pytest.MonkeyPatch) -> None:
    async def crossref_fail(doi: str):
        raise ProviderRemoteRateLimitError("limited", retry_after=5.0)

    async def datacite_should_not_run(doi: str):
        raise AssertionError("DataCite must not hide a Crossref attempted failure")

    monkeypatch.setattr(DEFAULT_CROSSREF_PROVIDER, "fetcher", crossref_fail)
    monkeypatch.setattr(DEFAULT_DATACITE_PROVIDER, "fetcher", datacite_should_not_run)

    report = await run_quick_research(
        kind=ResearchKind.URL,
        value="https://doi.org/10.5438/0012",
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        public_search_lookup=_no_public_search,
    )

    crossref_run = next(item for item in report.source_runs if item.source_name == "crossref_exact_work")
    assert crossref_run.state is SourceRunState.UNAVAILABLE
    assert crossref_run.reason is SourceRunReason.REMOTE_RATE_LIMIT
    assert crossref_run.execution_attempted is True
    assert all(item.source_name != "datacite_exact_doi" for item in report.source_runs)
    assert all(item.source != "datacite_exact_doi" for item in report.observations)


@pytest.mark.asyncio
async def test_datacite_attempted_failure_is_reported_after_crossref_no_match(monkeypatch: pytest.MonkeyPatch) -> None:
    async def crossref_missing(doi: str):
        return None

    async def datacite_limited(doi: str):
        raise ProviderRemoteRateLimitError("limited", retry_after=4.0)

    monkeypatch.setattr(DEFAULT_CROSSREF_PROVIDER, "fetcher", crossref_missing)
    monkeypatch.setattr(DEFAULT_DATACITE_PROVIDER, "fetcher", datacite_limited)

    report = await run_quick_research(
        kind=ResearchKind.URL,
        value="https://doi.org/10.5438/0012",
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        public_search_lookup=_no_public_search,
    )

    datacite_run = next(item for item in report.source_runs if item.source_name == "datacite_exact_doi")
    assert datacite_run.state is SourceRunState.UNAVAILABLE
    assert datacite_run.reason is SourceRunReason.REMOTE_RATE_LIMIT
    assert datacite_run.execution_attempted is True
    assert "DataCite exact-DOI fallback metadata was temporarily unavailable." in report.warnings
