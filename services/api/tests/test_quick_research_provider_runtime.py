# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import pytest

from app.models import Purpose
from app.providers import (
    ProviderObservationData,
    ProviderResult,
    ProviderValidationError,
)
from app.providers.registry import PROVIDER_BY_NAME
from app.research import ResearchKind, run_quick_research


async def _no_profile(_value: str):
    return None


async def _no_public_search(_value: str):
    return ()


@pytest.mark.asyncio
async def test_injected_sherlock_result_must_pass_runtime_source_locator_validation() -> None:
    class InvalidLocatorSherlock:
        descriptor = PROVIDER_BY_NAME["sherlock"]

        async def execute(self, query, secret):
            return ProviderResult(
                observations=(
                    ProviderObservationData(
                        source_locator="   ",
                        payload={
                            "site": "Synthetic",
                            "account_state": "claimed",
                        },
                    ),
                )
            )

    with pytest.raises(ProviderValidationError, match="source locator"):
        await run_quick_research(
            kind=ResearchKind.USERNAME,
            value="runtime-check",
            purpose=Purpose.SELF_AUDIT,
            consent_acknowledged=True,
            sherlock_provider=InvalidLocatorSherlock(),
            github_lookup=_no_profile,
            gitlab_lookup=_no_profile,
            codeforces_lookup=_no_profile,
            public_search_lookup=_no_public_search,
        )


@pytest.mark.asyncio
async def test_injected_sherlock_still_receives_normalized_username_through_runtime() -> None:
    class CapturingSherlock:
        descriptor = PROVIDER_BY_NAME["sherlock"]

        def __init__(self) -> None:
            self.values: list[str] = []

        async def execute(self, query, secret):
            self.values.append(query.identifier_value)
            return ProviderResult(observations=())

    provider = CapturingSherlock()
    report = await run_quick_research(
        kind=ResearchKind.USERNAME,
        value="CaseSensitiveHandle",
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        sherlock_provider=provider,
        github_lookup=_no_profile,
        gitlab_lookup=_no_profile,
        codeforces_lookup=_no_profile,
        public_search_lookup=_no_public_search,
    )

    assert provider.values == ["CaseSensitiveHandle"]
    assert report.normalized_value == "CaseSensitiveHandle"
