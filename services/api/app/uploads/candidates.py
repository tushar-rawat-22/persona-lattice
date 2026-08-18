# SPDX-License-Identifier: Apache-2.0
import re
from collections.abc import Sequence
from uuid import UUID, uuid4

from ..evidence import IdentifierKind, InvalidIdentifier, normalize_identifier
from .contracts import (
    CandidateOrigin,
    CandidateType,
    PageTextSpan,
    ReviewCandidate,
    ReviewStatus,
)


_EMAIL_RE = re.compile(
    r"(?<![\w.+-])([A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,63})(?![\w.-])"
)
_URL_RE = re.compile(r"\bhttps?://[^\s<>'\"\]\)]+", re.IGNORECASE)
_USERNAME_RE = re.compile(r"(?<![\w@])@([A-Za-z0-9._-]{2,64})")
_PHONE_RE = re.compile(r"(?<!\d)(\+\d[\d\s().-]{7,20}\d)(?!\d)")


class CandidateReviewError(ValueError):
    pass


def _source_page_for_span(
    source_start: int,
    source_end: int,
    page_spans: Sequence[PageTextSpan],
) -> int | None:
    matches = [
        span.page_number
        for span in page_spans
        if source_start >= span.source_start and source_end <= span.source_end
    ]
    return matches[0] if len(matches) == 1 else None


def _candidate(
    artifact_id: UUID,
    kind: IdentifierKind,
    raw_value: str,
    *,
    source_start: int,
    source_end: int,
    source_page: int | None = None,
) -> tuple[str, ReviewCandidate] | None:
    try:
        normalized = normalize_identifier(kind, raw_value)
    except InvalidIdentifier:
        return None

    key = f"{kind.value}:{normalized.comparison_key}"
    return (
        key,
        ReviewCandidate(
            candidate_id=uuid4(),
            candidate_type=CandidateType.IDENTIFIER,
            origin=CandidateOrigin.RULE,
            source_artifact_id=artifact_id,
            identifier_kind=kind,
            value=normalized.normalized_value,
            source_page=source_page,
            source_start=source_start,
            source_end=source_end,
        ),
    )


def extract_identifier_candidates(
    text: str,
    artifact_id: UUID,
    *,
    page_spans: Sequence[PageTextSpan] = (),
) -> list[ReviewCandidate]:
    found: dict[str, ReviewCandidate] = {}
    raw_matches: list[tuple[IdentifierKind, str, int, int]] = []

    for match in _EMAIL_RE.finditer(text):
        raw_matches.append((IdentifierKind.EMAIL, match.group(1), *match.span(1)))

    for match in _URL_RE.finditer(text):
        raw_value = match.group(0).rstrip(".,;:!?")
        raw_matches.append(
            (
                IdentifierKind.URL,
                raw_value,
                match.start(),
                match.start() + len(raw_value),
            )
        )

    for match in _USERNAME_RE.finditer(text):
        raw_matches.append(
            (
                IdentifierKind.USERNAME,
                f"@{match.group(1)}",
                match.start(),
                match.end(),
            )
        )

    for match in _PHONE_RE.finditer(text):
        raw_matches.append((IdentifierKind.PHONE, match.group(1), *match.span(1)))

    for kind, raw_value, source_start, source_end in raw_matches:
        result = _candidate(
            artifact_id,
            kind,
            raw_value,
            source_start=source_start,
            source_end=source_end,
            source_page=_source_page_for_span(source_start, source_end, page_spans),
        )
        if result is None:
            continue
        key, candidate = result
        found.setdefault(key, candidate)

    return [found[key] for key in sorted(found)]


def make_claim_candidate(
    *,
    artifact_id: UUID,
    statement: str,
    origin: CandidateOrigin = CandidateOrigin.AI,
) -> ReviewCandidate:
    value = statement.strip()
    if not value:
        raise CandidateReviewError("A claim candidate requires a statement.")
    return ReviewCandidate(
        candidate_id=uuid4(),
        candidate_type=CandidateType.CLAIM,
        origin=origin,
        source_artifact_id=artifact_id,
        value=value,
    )


def confirm_candidate(
    candidate: ReviewCandidate,
    *,
    human_confirmed: bool,
) -> ReviewCandidate:
    if not human_confirmed:
        raise CandidateReviewError("Human confirmation is required.")
    return candidate.model_copy(
        update={
            "review_status": ReviewStatus.CONFIRMED,
            "external_research_authorized": candidate.candidate_type
            == CandidateType.IDENTIFIER,
        }
    )


def reject_candidate(candidate: ReviewCandidate) -> ReviewCandidate:
    return candidate.model_copy(
        update={
            "review_status": ReviewStatus.REJECTED,
            "external_research_authorized": False,
        }
    )


def require_research_authorization(candidate: ReviewCandidate) -> None:
    if (
        candidate.candidate_type != CandidateType.IDENTIFIER
        or candidate.review_status != ReviewStatus.CONFIRMED
        or not candidate.external_research_authorized
    ):
        raise CandidateReviewError(
            "The candidate is not authorized for external research."
        )
