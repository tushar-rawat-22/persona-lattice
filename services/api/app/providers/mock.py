# SPDX-License-Identifier: Apache-2.0
from .base import ProviderDescriptor, ProviderObservationData, ProviderQuery, ProviderResult
from .registry import PROVIDER_BY_NAME


class SyntheticEchoProvider:
    descriptor: ProviderDescriptor = PROVIDER_BY_NAME["synthetic_echo"]

    async def execute(self, query: ProviderQuery, secret: str | None) -> ProviderResult:
        return ProviderResult(
            observations=(
                ProviderObservationData(
                    source_locator=f"synthetic://echo/{query.identifier_id}",
                    payload={
                        "synthetic": True,
                        "identifier_kind": query.identifier_kind,
                        "normalized_value": query.identifier_value,
                    },
                ),
            )
        )
