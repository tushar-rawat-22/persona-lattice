# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from ..evidence import IdentifierKind
from ..intelligence import LeadCandidate, LeadDisposition, LeadKind, LeadReason
from ..intelligence.contracts import canonicalize_lead
from .candidates import CandidateReviewError, require_research_authorization
from .contracts import ReviewCandidate


_LEAD_KIND_BY_IDENTIFIER_KIND = {
    IdentifierKind.USERNAME: LeadKind.USERNAME,
    IdentifierKind.EMAIL: LeadKind.EMAIL,
    IdentifierKind.PHONE: LeadKind.PHONE,
    IdentifierKind.URL: LeadKind.URL,
}


def _candidate_locator(candidate: ReviewCandidate) -> str:
    fragments = [f"candidate={candidate.candidate_id}"]
    if candidate.source_page is not None:
        fragments.append(f"page={candidate.source_page}")
    if candidate.source_start is not None and candidate.source_end is not None:
        fragments.append(f"offset={candidate.source_start}-{candidate.source_end}")
    return f"artifact://{candidate.source_artifact_id}#{'&'.join(fragments)}"


def promote_confirmed_identifier_candidate(candidate: ReviewCandidate) -> LeadCandidate:
    """Promote one explicitly reviewed upload identifier into the typed lead path.

    Extraction alone never calls this function. The caller must first complete
    the existing human-review step, which marks an identifier candidate as
    confirmed and externally research-authorized.
    """

    require_research_authorization(candidate)
    if candidate.identifier_kind is None:
        raise CandidateReviewError("A reviewed identifier candidate is missing its identifier kind.")

    lead_kind = _LEAD_KIND_BY_IDENTIFIER_KIND.get(candidate.identifier_kind)
    if lead_kind is None:
        raise CandidateReviewError(
            f"Reviewed {candidate.identifier_kind.value} candidates are not executable research leads."
        )

    value, comparison_key = canonicalize_lead(lead_kind, candidate.value)
    return LeadCandidate(
        kind=lead_kind,
        value=value,
        comparison_key=comparison_key,
        reason=LeadReason.REVIEWED_DOCUMENT_IDENTIFIER,
        disposition=LeadDisposition.AUTO_PIVOT,
        source="reviewed_upload_candidate",
        source_locator=_candidate_locator(candidate),
        field_name=candidate.identifier_kind.value,
    )
