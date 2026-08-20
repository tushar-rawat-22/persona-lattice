# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import pytest

from app.intelligence.source_states import SourceRunReason, SourceRunState
from app.models import Purpose
from app.providers.errors import ProviderResultValidationError, ProviderRemoteRateLimitError
from app.providers.shared_runtime import DEFAULT_STACK_OVERFLOW_PROVIDER
from app.research import ResearchKind, run_quick_research


async def _no_public_search(_value: str):
    return ()


async def _no_source(*args, **kwargs):
    return []


@pytest.mark.asyncio
async def test_exact_stack_overflow_profile_url_executes_shared_runtime(monkeypatch) -> None:
    async def fetcher(user_id: int) -> dict[str, object]:
        assert user_id == 12345
        return {
            "items": [
                {
                    "user_id": 12345,
                    "display_name": "Example User",
                    "reputation": 500,
                    "creation_date": 1_700_000_000,
                    "link": "https://stackoverflow.com/users/12345/example-user",
                    "about_me": "not retained",
                }
            ]
        }

    monkeypatch.setattr(DEFAULT_STACK_OVERFLOW_PROVIDER, "fetcher", fetcher)
    monkeypatch.setattr("app.research._dns_observations", _no_source)
    monkeypatch.setattr("app.research._wayback_observations", _no_source)

    report = await run_quick_research(
        kind=ResearchKind.URL,
        value="https://stackoverflow.com/users/12345/example-user",
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        public_search_lookup=_no_public_search,
    )

    observation = next(
        item for item in report.observations if item.source == "stack_overflow_public_profile"
    )
    assert observation.source_locator == "https://stackoverflow.com/users/12345/example-user"
    assert observation.details["stack_overflow_user_id"] == 12345
    assert observation.details["api_attribution"] == "Stack Overflow"
    assert observation.details["identity_claim"] is False
    assert "about_me" not in observation.details

    source_run = next(
        item for item in report.source_runs if item.source_name == "stack_overflow_public_profile"
    )
    assert source_run.state is SourceRunState.EXECUTED
    assert source_run.observation_count == 1
    assert source_run.execution_attempted is True


@pytest.mark.asyncio
async def test_ordinary_url_does_not_attempt_stack_overflow_provider(monkeypatch) -> None:
    async def should_not_run(user_id: int) -> dict[str, object]:
        raise AssertionError("Stack Overflow provider must not run for an ordinary URL")

    monkeypatch.setattr(DEFAULT_STACK_OVERFLOW_PROVIDER, "fetcher", should_not_run)
    monkeypatch.setattr("app.research._dns_observations", _no_source)
    monkeypatch.setattr("app.research._wayback_observations", _no_source)

    report = await run_quick_research(
        kind=ResearchKind.URL,
        value="https://example.com/public-page",
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        public_search_lookup=_no_public_search,
    )

    assert all(item.source != "stack_overflow_public_profile" for item in report.observations)
    assert all(item.source_name != "stack_overflow_public_profile" for item in report.source_runs)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("exc", "expected_reason"),
    [
        (ProviderRemoteRateLimitError("remote limit", retry_after=3.0), SourceRunReason.REMOTE_RATE_LIMIT),
        (ProviderResultValidationError("bad returned user"), SourceRunReason.MALFORMED_RESULT),
    ],
)
async def test_stack_overflow_runtime_preserves_attempted_failure_phase(
    monkeypatch,
    exc,
    expected_reason,
) -> None:
    async def fail(*args, **kwargs):
        raise exc

    monkeypatch.setattr("app.research._stack_overflow_observations", fail)
    monkeypatch.setattr("app.research._dns_observations", _no_source)
    monkeypatch.setattr("app.research._wayback_observations", _no_source)

    report = await run_quick_research(
        kind=ResearchKind.URL,
        value="https://stackoverflow.com/users/12345/example-user",
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        public_search_lookup=_no_public_search,
    )

    source_run = next(
        item for item in report.source_runs if item.source_name == "stack_overflow_public_profile"
    )
    assert source_run.state is SourceRunState.UNAVAILABLE
    assert source_run.reason is expected_reason
    assert source_run.execution_attempted is True
    assert "Stack Overflow public-profile metadata was temporarily unavailable." in report.warnings
