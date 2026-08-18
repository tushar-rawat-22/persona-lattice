# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from ..cases import CASE_STORE, CaseStore, StoredCase
from ..convergence import build_converged_payload, run_converged_research
from ..models import Purpose
from ..policy import enforce_purpose
from ..research import ResearchKind, run_quick_research
from .review_service import promote_stored_candidate


class ReviewedCandidateCaseMode(StrEnum):
    QUICK = "quick"
    CONVERGED = "converged"


def _seed_provenance(source_locator: str) -> dict[str, object]:
    return {
        "source": "reviewed_upload_candidate",
        "source_locator": source_locator,
        "human_reviewed": True,
    }


async def run_reviewed_candidate_case(
    artifact_id: UUID,
    candidate_id: UUID,
    *,
    mode: ReviewedCandidateCaseMode,
    purpose: Purpose,
    consent_acknowledged: bool,
    case_store: CaseStore = CASE_STORE,
) -> StoredCase:
    """Run a retained case from the current server-owned reviewed candidate.

    The candidate is reloaded and revalidated at this execution boundary. Review
    and promotion remain separate actions; calling either one does not reach this
    function or trigger provider traffic.
    """

    enforce_purpose(purpose, consent_acknowledged)
    lead = promote_stored_candidate(artifact_id, candidate_id)
    research_kind = ResearchKind(lead.kind.value)
    provenance = _seed_provenance(lead.source_locator)

    if mode is ReviewedCandidateCaseMode.QUICK:
        report = await run_quick_research(
            kind=research_kind,
            value=lead.value,
            purpose=purpose,
            consent_acknowledged=consent_acknowledged,
        )
        return case_store.create(
            seed_kind=report.kind,
            seed_value=report.normalized_value,
            report=report,
            seed_provenance=provenance,
        )

    report = await run_converged_research(
        kind=research_kind,
        value=lead.value,
        purpose=purpose,
        consent_acknowledged=consent_acknowledged,
    )
    report_payload = {
        "kind": report.seed_kind.value,
        "normalized_value": report.seed_value,
        "seed_provenance": provenance,
        "converged_report": build_converged_payload(report),
    }
    return case_store.create_payload(
        seed_kind=report.seed_kind,
        seed_value=report.seed_value,
        report_payload=report_payload,
    )
