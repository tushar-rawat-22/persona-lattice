# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from uuid import UUID

from ..intelligence.sec_edgar_admission import sec_cik_from_submissions_url
from ..models import Purpose
from .base import ProviderQuery, ProviderResult
from .contracts import ExecutionRequest
from .shared_runtime import DEFAULT_PROVIDER_RUNTIME, DEFAULT_SEC_EDGAR_PROVIDER


async def execute_sec_edgar_exact_url(
    normalized_value: str,
    *,
    subject_id: UUID,
    identifier_id: UUID,
    purpose: Purpose,
    consent_acknowledged: bool,
) -> ProviderResult | None:
    """Execute the process-owned SEC adapter only for an exact admitted URL.

    Returning ``None`` means the supplied URL is outside the SEC admission
    shape and therefore must not create a source run or consume provider
    budget. Provider/configuration failures are intentionally not translated
    here; the quick-research orchestration owns phase-correct source-state and
    warning mapping just like the other exact URL sources.
    """

    if sec_cik_from_submissions_url(normalized_value) is None:
        return None

    request = ExecutionRequest(
        provider_name=DEFAULT_SEC_EDGAR_PROVIDER.descriptor.name,
        subject_id=subject_id,
        identifier_id=identifier_id,
        purpose=purpose,
        consent_acknowledged=consent_acknowledged,
    )
    return await DEFAULT_PROVIDER_RUNTIME.execute(
        request=request,
        query=ProviderQuery(
            subject_id=subject_id,
            identifier_id=identifier_id,
            identifier_kind="url",
            identifier_value=normalized_value,
        ),
    )
