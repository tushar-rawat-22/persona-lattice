# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from dataclasses import replace
from uuid import uuid4

import pytest

from app.models import Purpose
from app.providers import (
    ExecutionRequest,
    ProviderObservationData,
    ProviderQuery,
    ProviderResult,
    SyntheticEchoProvider,
)
from app.providers.errors import ProviderResultValidationError
from app.providers.runtime import ProviderRuntime


class LocatorProvider:
    def __init__(self, locator: str) -> None:
        self.locator = locator
        self.descriptor = replace(
            SyntheticEchoProvider.descriptor,
            name="locator-hardening-test",
            max_attempts=1,
        )

    async def execute(self, query, secret):
        assert secret is None
        return ProviderResult(
            observations=(
                ProviderObservationData(
                    source_locator=self.locator,
                    payload={"ok": True},
                ),
            )
        )


def _request() -> ExecutionRequest:
    return ExecutionRequest(
        provider_name="locator-hardening-test",
        subject_id=uuid4(),
        identifier_id=uuid4(),
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
    )


def _query(request: ExecutionRequest) -> ProviderQuery:
    return ProviderQuery(
        subject_id=request.subject_id,
        identifier_id=request.identifier_id,
        identifier_kind="email",
        identifier_value="person@example.test",
    )


async def _execute(locator: str) -> ProviderResult:
    provider = LocatorProvider(locator)
    runtime = ProviderRuntime(adapters=[provider])
    request = _request()
    return await runtime.execute(request=request, query=_query(request))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "locator",
    [
        "https://example.test/profile",
        "http://example.test/public?id=42",
        "synthetic://fixture/account",
        "sherlock://site/GitHub",
        "dns://example.test",
        "local://libphonenumber",
    ],
)
async def test_runtime_accepts_canonical_source_locators(locator: str) -> None:
    result = await _execute(locator)
    assert result.observations[0].source_locator == locator


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("locator", "message"),
    [
        (" https://example.test/profile", "canonical source locator"),
        ("https://example.test/profile\n", "canonical source locator"),
        ("https://example.test/\x00profile", "control characters"),
        ("example.test/profile", "explicit scheme"),
        ("https://user:password@example.test/profile", "must not embed credentials"),
        ("https:///missing-host", "requires a hostname"),
    ],
)
async def test_runtime_rejects_malformed_or_sensitive_source_locators(
    locator: str,
    message: str,
) -> None:
    with pytest.raises(ProviderResultValidationError, match=message):
        await _execute(locator)


@pytest.mark.asyncio
async def test_runtime_rejects_oversized_source_locator() -> None:
    locator = "https://example.test/" + ("a" * 5000)
    with pytest.raises(ProviderResultValidationError, match="exceeds the configured limit"):
        await _execute(locator)
