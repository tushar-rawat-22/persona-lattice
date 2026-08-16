# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import json
import os
from typing import Any

from .base import AuthMode, Provider, ProviderDescriptor, ProviderQuery, ProviderResult
from .contracts import ExecutionRequest
from .errors import (
    ProviderAuthError,
    ProviderExecutionError,
    ProviderRemoteRateLimitError,
    ProviderResponseTooLarge,
    ProviderTimeoutError,
    ProviderValidationError,
)
from .policy import authorize_execution
from .rate_limit import RateBudget


Sleep = Callable[[float], Awaitable[None]]
SecretResolver = Callable[[str], str | None]


def _environment_secret(name: str) -> str | None:
    return os.environ.get(name)


def _serialized_size(result: ProviderResult) -> int:
    payload: dict[str, Any] = {
        "observations": [
            {"source_locator": item.source_locator, "payload": item.payload}
            for item in result.observations
        ]
    }
    try:
        serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ProviderValidationError("Provider result is not JSON serializable.") from exc
    return len(serialized)


@dataclass(frozen=True, slots=True)
class PreparedProviderExecution:
    """Policy-authorized provider selection without a network call or secret read.

    The object is created only by `ProviderRuntime.prepare()`. Store-specific
    validation may safely happen after preparation and before the remote call,
    preserving the existing fail-closed ordering where execution policy is
    checked before subject/identifier lookup details can affect the response.
    """

    request: ExecutionRequest
    adapter: Provider
    descriptor: ProviderDescriptor


class ProviderRuntime:
    """Reusable M3 provider execution controls independent of evidence storage.

    This is an extraction of the existing ProviderExecutor runtime, not a second
    provider framework. It owns policy authorization, server-side credentials,
    rate/concurrency budgets, bounded retries/timeouts, result-contract checks and
    response-size/source-locator validation. Persistence remains the caller's job.
    """

    def __init__(
        self,
        *,
        adapters: list[Provider],
        secret_resolver: SecretResolver = _environment_secret,
        sleep: Sleep = asyncio.sleep,
        rate_clock=None,
    ) -> None:
        names = [adapter.descriptor.name for adapter in adapters]
        if len(names) != len(set(names)):
            raise ValueError("Provider adapter names must be unique.")

        self.adapters = {adapter.descriptor.name: adapter for adapter in adapters}
        self.secret_resolver = secret_resolver
        self.sleep = sleep
        self._semaphores = {
            adapter.descriptor.name: asyncio.Semaphore(adapter.descriptor.max_concurrency)
            for adapter in adapters
        }
        self._rate_budgets = {
            adapter.descriptor.name: RateBudget(
                limit=adapter.descriptor.rate_limit,
                window_seconds=adapter.descriptor.rate_window_seconds,
                **({"clock": rate_clock} if rate_clock is not None else {}),
            )
            for adapter in adapters
        }

    def prepare(self, request: ExecutionRequest) -> PreparedProviderExecution:
        """Select and authorize a provider without touching credentials/network."""

        adapter = self.adapters.get(request.provider_name)
        if adapter is None:
            raise ProviderValidationError("Provider is not registered for execution.")
        descriptor = adapter.descriptor
        authorize_execution(descriptor, request)
        return PreparedProviderExecution(
            request=request,
            adapter=adapter,
            descriptor=descriptor,
        )

    async def execute(
        self,
        *,
        request: ExecutionRequest,
        query: ProviderQuery,
    ) -> ProviderResult:
        """Authorize and execute one provider query without persisting observations."""

        prepared = self.prepare(request)
        return await self.execute_prepared(prepared=prepared, query=query)

    async def execute_prepared(
        self,
        *,
        prepared: PreparedProviderExecution,
        query: ProviderQuery,
    ) -> ProviderResult:
        """Execute a previously policy-authorized provider selection.

        This method validates that the query still belongs to the authorized
        request. A caller cannot prepare one subject/provider and substitute a
        different query afterward.
        """

        request = prepared.request
        adapter = prepared.adapter
        descriptor = prepared.descriptor

        if self.adapters.get(descriptor.name) is not adapter:
            raise ProviderValidationError("Prepared provider is not owned by this runtime.")
        if request.provider_name != descriptor.name or adapter.descriptor != descriptor:
            raise ProviderValidationError("Prepared provider execution is inconsistent.")
        if query.subject_id != request.subject_id or query.identifier_id != request.identifier_id:
            raise ProviderValidationError("Provider query does not match the authorized request.")
        if (
            descriptor.supported_identifier_kinds
            and query.identifier_kind not in descriptor.supported_identifier_kinds
        ):
            raise ProviderValidationError(
                "Identifier kind is not supported by the requested provider."
            )
        if not query.identifier_value.strip():
            raise ProviderValidationError("Provider query identifier value is empty.")

        secret: str | None = None
        if descriptor.auth_mode is AuthMode.API_KEY:
            assert descriptor.secret_env is not None
            secret = self.secret_resolver(descriptor.secret_env)
            if not secret:
                raise ProviderAuthError("Provider credential is not configured server-side.")

        result: ProviderResult | None = None
        last_error: ProviderExecutionError | None = None

        for attempt in range(1, descriptor.max_attempts + 1):
            try:
                self._rate_budgets[descriptor.name].consume()
                async with self._semaphores[descriptor.name]:
                    result = await asyncio.wait_for(
                        adapter.execute(query, secret),
                        timeout=descriptor.timeout_seconds,
                    )
                if not isinstance(result, ProviderResult):
                    raise ProviderValidationError("Provider returned an invalid result contract.")
                break
            except asyncio.TimeoutError as exc:
                last_error = ProviderTimeoutError("Provider call timed out.")
                last_error.__cause__ = exc
            except ProviderExecutionError as exc:
                last_error = exc
            except Exception as exc:
                raise ProviderExecutionError("Provider adapter failed unexpectedly.") from exc

            if last_error is None or not last_error.retryable or attempt >= descriptor.max_attempts:
                assert last_error is not None
                raise last_error

            base_delay = min(0.25 * (2 ** (attempt - 1)), 2.0)
            if isinstance(last_error, ProviderRemoteRateLimitError) and last_error.retry_after:
                base_delay = min(max(last_error.retry_after, base_delay), 2.0)
            await self.sleep(base_delay)

        if result is None:
            if last_error is not None:
                raise last_error
            raise ProviderExecutionError("Provider returned no result.")

        if _serialized_size(result) > descriptor.max_response_bytes:
            raise ProviderResponseTooLarge("Provider response exceeds the configured size limit.")

        for observation in result.observations:
            if not observation.source_locator.strip():
                raise ProviderValidationError("Provider observation requires a source locator.")

        return result
