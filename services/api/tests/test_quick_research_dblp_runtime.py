# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import pytest

from app.intelligence.source_states import SourceRunReason, SourceRunState
from app.models import Purpose
from app.providers.errors import ProviderResultValidationError, ProviderRemoteRateLimitError
from app.providers.shared_runtime import DEFAULT_DBLP_PROVIDER
from app.research import ResearchKind, run_quick_research


PID = "65/9612-1"
PID_URL = f"https://dblp.org/pid/{PID}"


async def _no_public_search(_value: str):
    return ()


async def _no_source(*args, **kwargs):
    return []


def _payload() -> dict[str, object]:
    return {
        "head": {"vars": ["person", "name"]},
        "results": {
            "bindings": [
                {
                    "person": {"type": "uri", "value": PID_URL},
                    "name": {"type": "literal", "value": "François Gauthier"},
                }
            ]
        },
    }


@pytest.mark.asyncio
async def test_exact_dblp_pid_url_executes_shared_runtime(monkeypatch) -> None:
    async def fetcher(pid: str) -> dict[str, object]:
        assert pid == PID
        return _payload()

    monkeypatch.setattr(DEFAULT_DBLP_PROVIDER, "fetcher", fetcher)
    monkeypatch.setattr("app.research._dns_observations", _no_source)
    monkeypatch.setattr("app.research._wayback_observations", _no_source)

    report = await run_quick_research(
        kind=ResearchKind.URL,
        value=PID_URL,
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        public_search_lookup=_no_public_search,
    )

    observation = next(item for item in report.observations if item.source == "dblp_exact_person")
    assert observation.source_locator == PID_URL
    assert observation.details == {
        "dblp_pid": PID_URL,
        "dblp_primary_name": "François Gauthier",
        "data_license": "CC0",
        "api_attribution": "dblp computer science bibliography",
        "identity_claim": False,
    }
    source_run = next(item for item in report.source_runs if item.source_name == "dblp_exact_person")
    assert source_run.state is SourceRunState.EXECUTED
    assert source_run.observation_count == 1
    assert source_run.execution_attempted is True


@pytest.mark.asyncio
async def test_ordinary_url_does_not_attempt_dblp_provider(monkeypatch) -> None:
    async def should_not_run(pid: str):
        raise AssertionError("DBLP provider must not run for an ordinary URL")

    monkeypatch.setattr(DEFAULT_DBLP_PROVIDER, "fetcher", should_not_run)
    monkeypatch.setattr("app.research._dns_observations", _no_source)
    monkeypatch.setattr("app.research._wayback_observations", _no_source)

    report = await run_quick_research(
        kind=ResearchKind.URL,
        value="https://example.com/public-page",
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        public_search_lookup=_no_public_search,
    )
    assert all(item.source != "dblp_exact_person" for item in report.observations)
    assert all(item.source_name != "dblp_exact_person" for item in report.source_runs)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("exc", "expected_reason"),
    [
        (ProviderRemoteRateLimitError("remote limit", retry_after=3.0), SourceRunReason.REMOTE_RATE_LIMIT),
        (ProviderResultValidationError("bad returned person"), SourceRunReason.MALFORMED_RESULT),
    ],
)
async def test_dblp_runtime_preserves_attempted_failure_phase(monkeypatch, exc, expected_reason) -> None:
    async def fail(*args, **kwargs):
        raise exc

    monkeypatch.setattr("app.research._dblp_observations", fail)
    monkeypatch.setattr("app.research._dns_observations", _no_source)
    monkeypatch.setattr("app.research._wayback_observations", _no_source)

    report = await run_quick_research(
        kind=ResearchKind.URL,
        value=PID_URL,
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        public_search_lookup=_no_public_search,
    )

    source_run = next(item for item in report.source_runs if item.source_name == "dblp_exact_person")
    assert source_run.state is SourceRunState.UNAVAILABLE
    assert source_run.reason is expected_reason
    assert source_run.execution_attempted is True
    assert "DBLP exact-person metadata was temporarily unavailable." in report.warnings
