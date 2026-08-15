# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import json
import os
from typing import Any

from ..evidence import EvidenceStore, Observation, ObservationSourceKind
from ..uploads import CandidateType
from .base import AuthMode, Provider, ProviderQuery, ProviderResult
from .contracts import ExecutionRequest, QueryOrigin
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
    return len(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8"))


class ProviderExecutor:
    def __init__(
        self,
        *,
        store: EvidenceStore,
        adapters: list[Provider],
        secret_resolver: SecretResolver = _environment_secret,
        sleep: Sleep = asyncio.sleep,
        rate_clock=None,
    ) -> None:
        self.store = store
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

    async def execute(self, request: ExecutionRequest) -> list[Observation]:
        adapter = self.adapters.get(request.provider_name)
        if adapter is None:
            raise ProviderValidationError("Provider is not registered for execution.")

        descriptor = adapter.descriptor
        authorize_execution(descriptor, request)
        subject = self.store.get_subject(request.subject_id)
        identifier = self.store.get_identifier(request.identifier_id)
        if identifier.subject_id != subject.id:
            raise ProviderValidationError("Identifier does not belong to the requested subject.")

        if request.query_origin is QueryOrigin.CONFIRMED_DOCUMENT_CANDIDATE:
            candidate = request.document_candidate
            if candidate is None or candidate.candidate_type is not CandidateType.IDENTIFIER:
                raise ProviderValidationError("A confirmed identifier candidate is required.")
            if candidate.identifier_kind is not identifier.kind:
                raise ProviderValidationError("Candidate identifier kind does not match stored identifier.")
            if candidate.value != identifier.normalized_value:
                raise ProviderValidationError("Candidate identifier value does not match stored identifier.")

        secret: str | None = None
        if descriptor.auth_mode is AuthMode.API_KEY:
            if not descriptor.secret_env:
                raise ProviderAuthError("Provider secret configuration is incomplete.")
            secret = self.secret_resolver(descriptor.secret_env)
            if not secret:
                raise ProviderAuthError("Provider credential is not configured server-side.")

        self._rate_budgets[descriptor.name].consume()
        query = ProviderQuery(
            subject_id=subject.id,
            identifier_id=identifier.id,
            identifier_kind=identifier.kind.value,
            identifier_value=identifier.normalized_value,
        )

        result: ProviderResult | None = None
        last_error: ProviderExecutionError | None = None

        for attempt in range(1, descriptor.max_attempts + 1):
            try:
                async with self._semaphores[descriptor.name]:
                    result = await asyncio.wait_for(
                        adapter.execute(query, secret),
                        timeout=descriptor.timeout_seconds,
                    )
                break
            except asyncio.TimeoutError as exc:
                last_error = ProviderTimeoutError("Provider call timed out.")
                last_error.__cause__ = exc
            except ProviderExecutionError as exc:
                last_error = exc

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

        observations: list[Observation] = []
        for item in result.observations:
            if not item.source_locator.strip():
                raise ProviderValidationError("Provider observation requires a source locator.")
            observation = self.store.add_observation(
                subject_id=subject.id,
                identifier_id=identifier.id,
                source_kind=ObservationSourceKind.PROVIDER,
                source_name=descriptor.name,
                source_locator=item.source_locator,
                payload={
                    **item.payload,
                    "provider": descriptor.name,
                    "provider_version": descriptor.version,
                    "source_category": descriptor.source_category.value,
                },
            )
            observations.append(observation)
        return observations
