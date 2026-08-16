# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from dataclasses import replace
from uuid import uuid4

import pytest

from app.models import Purpose
from app.providers import (
    AuthMode,
    ExecutionRequest,
    PreparedProviderExecution,
    ProviderAuthError,
    ProviderObservationData,
    ProviderPolicyError,
    ProviderQuery,
    ProviderResult,
    ProviderValidationError,
    SyntheticEchoProvider,
)
from app.providers.runtime import ProviderRuntime


def _request(provider_name: str = "synthetic_echo", **overrides) -> ExecutionRequest:
    values = {
        "provider_name": provider_name,
        "subject_id": uuid4(),
        "identifier_id": uuid4(),
        "purpose": Purpose.SELF_AUDIT,
        "consent_acknowledged": True,
    }
    values.update(overrides)
    return ExecutionRequest(**values)


def _query(request: ExecutionRequest, **overrides) -> ProviderQuery:
    values = {
        "subject_id": request.subject_id,
        "identifier_id": request.identifier_id,
        "identifier_kind": "email",
        "identifier_value": "person@example.test",
    }
    values.update(overrides)
    return ProviderQuery(**values)


@pytest.mark.asyncio
async def test_runtime_executes_governed_provider_without_evidence_store() -> None:
    request = _request()
    runtime = ProviderRuntime(adapters=[SyntheticEchoProvider()])

    result = await runtime.execute(request=request, query=_query(request))

    assert isinstance(result, ProviderResult)
    assert len(result.observations) == 1
    assert result.observations[0].source_locator.startswith("synthetic://")
    assert result.observations[0].payload["synthetic"] is True


@pytest.mark.asyncio
async def test_runtime_rejects_query_subject_or_identifier_substitution() -> None:
    request = _request()
    runtime = ProviderRuntime(adapters=[SyntheticEchoProvider()])

    with pytest.raises(ProviderValidationError, match="authorized request"):
        await runtime.execute(
            request=request,
            query=_query(request, subject_id=uuid4()),
        )

    with pytest.raises(ProviderValidationError, match="authorized request"):
        await runtime.execute(
            request=request,
            query=_query(request, identifier_id=uuid4()),
        )


@pytest.mark.asyncio
async def test_runtime_rejects_unsupported_identifier_kind_before_adapter_call() -> None:
    class CountingProvider:
        def __init__(self) -> None:
            self.calls = 0
            self.descriptor = replace(
                SyntheticEchoProvider.descriptor,
                name="username-only",
                supported_identifier_kinds=frozenset({"username"}),
            )

        async def execute(self, query, secret):
            self.calls += 1
            return ProviderResult(observations=())

    provider = CountingProvider()
    request = _request(provider_name="username-only")
    runtime = ProviderRuntime(adapters=[provider])

    with pytest.raises(ProviderValidationError, match="not supported"):
        await runtime.execute(request=request, query=_query(request))
    assert provider.calls == 0


def test_prepare_runs_policy_before_any_secret_resolution() -> None:
    class AuthProvider:
        descriptor = replace(
            SyntheticEchoProvider.descriptor,
            name="auth-policy",
            auth_mode=AuthMode.API_KEY,
            secret_env="SYNTHETIC_API_KEY",
            allowed_purposes=frozenset({Purpose.PUBLIC_SOURCE_RESEARCH}),
        )

        async def execute(self, query, secret):
            return ProviderResult(observations=())

    secret_reads: list[str] = []
    runtime = ProviderRuntime(
        adapters=[AuthProvider()],
        secret_resolver=lambda name: secret_reads.append(name) or "secret",
    )
    request = _request(provider_name="auth-policy", purpose=Purpose.SELF_AUDIT)

    with pytest.raises(ProviderPolicyError):
        runtime.prepare(request)
    assert secret_reads == []


@pytest.mark.asyncio
async def test_runtime_resolves_secret_server_side_and_never_places_it_in_query() -> None:
    class AuthProvider:
        descriptor = replace(
            SyntheticEchoProvider.descriptor,
            name="auth-runtime",
            auth_mode=AuthMode.API_KEY,
            secret_env="SYNTHETIC_API_KEY",
        )

        def __init__(self) -> None:
            self.seen_secret: str | None = None
            self.seen_value: str | None = None

        async def execute(self, query, secret):
            self.seen_secret = secret
            self.seen_value = query.identifier_value
            return ProviderResult(
                observations=(
                    ProviderObservationData(
                        source_locator="synthetic://auth-runtime",
                        payload={"ok": True},
                    ),
                )
            )

    provider = AuthProvider()
    request = _request(provider_name="auth-runtime")
    runtime = ProviderRuntime(
        adapters=[provider],
        secret_resolver=lambda name: "server-secret" if name == "SYNTHETIC_API_KEY" else None,
    )

    result = await runtime.execute(request=request, query=_query(request))

    assert result.observations[0].payload == {"ok": True}
    assert provider.seen_secret == "server-secret"
    assert provider.seen_value == "person@example.test"


@pytest.mark.asyncio
async def test_runtime_missing_secret_fails_before_adapter_call() -> None:
    class AuthProvider:
        descriptor = replace(
            SyntheticEchoProvider.descriptor,
            name="missing-auth-runtime",
            auth_mode=AuthMode.API_KEY,
            secret_env="SYNTHETIC_API_KEY",
        )

        def __init__(self) -> None:
            self.calls = 0

        async def execute(self, query, secret):
            self.calls += 1
            return ProviderResult(observations=())

    provider = AuthProvider()
    request = _request(provider_name="missing-auth-runtime")
    runtime = ProviderRuntime(adapters=[provider], secret_resolver=lambda _name: None)

    with pytest.raises(ProviderAuthError):
        await runtime.execute(request=request, query=_query(request))
    assert provider.calls == 0


@pytest.mark.asyncio
async def test_prepared_execution_cannot_cross_runtime_instance() -> None:
    adapter = SyntheticEchoProvider()
    first = ProviderRuntime(adapters=[adapter])
    second = ProviderRuntime(adapters=[SyntheticEchoProvider()])
    request = _request()
    prepared = first.prepare(request)

    with pytest.raises(ProviderValidationError, match="not owned"):
        await second.execute_prepared(prepared=prepared, query=_query(request))


@pytest.mark.asyncio
async def test_forged_prepared_execution_cannot_bypass_policy() -> None:
    adapter = SyntheticEchoProvider()
    runtime = ProviderRuntime(adapters=[adapter])
    request = _request(consent_acknowledged=False)
    forged = PreparedProviderExecution(
        request=request,
        adapter=adapter,
        descriptor=adapter.descriptor,
    )

    with pytest.raises(ProviderPolicyError, match="requires consent"):
        await runtime.execute_prepared(prepared=forged, query=_query(request))
