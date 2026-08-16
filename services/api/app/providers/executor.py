# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import os

from ..evidence import EvidenceStore, Observation, ObservationSourceKind
from ..uploads import CandidateType
from .base import Provider, ProviderQuery
from .contracts import ExecutionRequest, QueryOrigin
from .errors import ProviderValidationError
from .runtime import ProviderRuntime


Sleep = Callable[[float], Awaitable[None]]
SecretResolver = Callable[[str], str | None]


def _environment_secret(name: str) -> str | None:
    return os.environ.get(name)


class ProviderExecutor:
    """Persistent M3 provider executor backed by the reusable ProviderRuntime.

    Store ownership/candidate validation and M1 observation persistence stay here.
    Network/policy/credential/retry/resource controls live in ProviderRuntime so
    ephemeral research can reuse the same governed execution semantics later.
    """

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
        self.runtime = ProviderRuntime(
            adapters=adapters,
            secret_resolver=secret_resolver,
            sleep=sleep,
            rate_clock=rate_clock,
        )
        # Preserve the existing public-ish attribute used by maintainers/tests.
        self.adapters = self.runtime.adapters

    async def execute(self, request: ExecutionRequest) -> list[Observation]:
        # Keep policy authorization ahead of subject/identifier lookup. This
        # preserves the old fail-closed ordering and avoids exposing store details
        # to a request that should never be eligible for execution.
        prepared = self.runtime.prepare(request)
        descriptor = prepared.descriptor

        subject = self.store.get_subject(request.subject_id)
        identifier = self.store.get_identifier(request.identifier_id)
        if identifier.subject_id != subject.id:
            raise ProviderValidationError("Identifier does not belong to the requested subject.")
        if (
            descriptor.supported_identifier_kinds
            and identifier.kind.value not in descriptor.supported_identifier_kinds
        ):
            raise ProviderValidationError(
                "Identifier kind is not supported by the requested provider."
            )

        if request.query_origin is QueryOrigin.CONFIRMED_DOCUMENT_CANDIDATE:
            candidate = request.document_candidate
            if candidate is None or candidate.candidate_type is not CandidateType.IDENTIFIER:
                raise ProviderValidationError("A confirmed identifier candidate is required.")
            if candidate.identifier_kind is not identifier.kind:
                raise ProviderValidationError("Candidate identifier kind does not match stored identifier.")
            if candidate.value != identifier.normalized_value:
                raise ProviderValidationError("Candidate identifier value does not match stored identifier.")

        query = ProviderQuery(
            subject_id=subject.id,
            identifier_id=identifier.id,
            identifier_kind=identifier.kind.value,
            identifier_value=identifier.normalized_value,
        )
        result = await self.runtime.execute_prepared(prepared=prepared, query=query)

        observations: list[Observation] = []
        for item in result.observations:
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
