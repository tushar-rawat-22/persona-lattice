# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from collections.abc import Awaitable, Callable

from ..intelligence.sec_edgar_admission import (
    SecEdgarAdmissionError,
    bounded_sec_submissions_metadata,
    sec_cik_from_submissions_url,
    sec_submissions_url,
)
from .base import ProviderDescriptor, ProviderObservationData, ProviderQuery, ProviderResult
from .errors import (
    ProviderConfigurationError,
    ProviderResultValidationError,
    ProviderValidationError,
)
from .sec_edgar_config import sec_edgar_user_agent_from_env
from .sec_edgar_transport import fetch_sec_submissions


SecEdgarFetch = Callable[..., Awaitable[dict[str, object] | None]]
SecUserAgentLoader = Callable[[], str | None]


class SecEdgarExactCikProvider:
    """Bounded exact-CIK SEC EDGAR provider.

    The descriptor is injected until the registry activation slice lands. This
    keeps transport/provider behavior independently testable without creating a
    second policy authority. Production construction must pass the canonical
    descriptor from ``PROVIDER_BY_NAME``.
    """

    def __init__(
        self,
        *,
        descriptor: ProviderDescriptor,
        fetcher: SecEdgarFetch = fetch_sec_submissions,
        user_agent_loader: SecUserAgentLoader = sec_edgar_user_agent_from_env,
    ) -> None:
        self.descriptor = descriptor
        self.fetcher = fetcher
        self.user_agent_loader = user_agent_loader

    async def execute(self, query: ProviderQuery, secret: str | None) -> ProviderResult:
        if secret is not None:
            raise ProviderValidationError("SEC EDGAR exact-CIK lookup does not accept credentials.")
        if query.identifier_kind != "url":
            raise ProviderValidationError("SEC EDGAR exact-CIK lookup only accepts URLs.")

        cik = sec_cik_from_submissions_url(query.identifier_value)
        if cik is None:
            raise ProviderValidationError(
                "SEC EDGAR exact-CIK lookup requires a canonical submissions URL."
            )

        user_agent = self.user_agent_loader()
        if user_agent is None:
            raise ProviderConfigurationError(
                "SEC EDGAR operator User-Agent is not configured."
            )

        payload = await self.fetcher(cik, user_agent=user_agent)
        if payload is None:
            return ProviderResult(observations=())
        try:
            details = bounded_sec_submissions_metadata(payload, expected_cik=cik)
        except SecEdgarAdmissionError as exc:
            raise ProviderResultValidationError(
                "SEC EDGAR submissions response violated the admitted metadata contract."
            ) from exc

        return ProviderResult(
            observations=(
                ProviderObservationData(
                    source_locator=sec_submissions_url(cik),
                    payload=details,
                ),
            )
        )
