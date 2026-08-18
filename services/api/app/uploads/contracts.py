# SPDX-License-Identifier: Apache-2.0
from enum import Enum
from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from ..evidence import IdentifierKind


class CandidateType(str, Enum):
    IDENTIFIER = "identifier"
    CLAIM = "claim"


class CandidateOrigin(str, Enum):
    RULE = "rule"
    AI = "ai"


class ReviewStatus(str, Enum):
    PENDING = "pending_human_review"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class PageTextSpan(BaseModel):
    """One PDF page's exact character interval inside flattened extracted text."""

    page_number: int = Field(ge=1)
    source_start: int = Field(ge=0)
    source_end: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_span(self) -> Self:
        if self.source_end < self.source_start:
            raise ValueError("Page source_end cannot be before source_start.")
        return self


class ReviewCandidate(BaseModel):
    candidate_id: UUID
    candidate_type: CandidateType
    origin: CandidateOrigin
    source_artifact_id: UUID
    identifier_kind: IdentifierKind | None = None
    value: str
    source_page: int | None = Field(default=None, ge=1)
    source_start: int | None = Field(default=None, ge=0)
    source_end: int | None = Field(default=None, ge=0)
    review_status: ReviewStatus = ReviewStatus.PENDING
    external_research_authorized: bool = False

    @model_validator(mode="after")
    def validate_source_span(self) -> Self:
        if (self.source_start is None) != (self.source_end is None):
            raise ValueError("Candidate source offsets must be supplied together.")
        if self.source_start is not None and self.source_end is not None:
            if self.source_end <= self.source_start:
                raise ValueError("Candidate source_end must be greater than source_start.")
        if self.source_page is not None and self.source_start is None:
            raise ValueError("Candidate source_page requires source offsets.")
        return self


class ArtifactPreview(BaseModel):
    artifact_id: UUID
    original_name: str
    size_bytes: int
    sha256: str
    detected_media_type: str
    extraction_method: str
    extracted_text: str
    extracted_chars: int
    page_spans: list[PageTextSpan] = Field(default_factory=list)
    trust_boundary: Literal["untrusted_uploaded_content"] = "untrusted_uploaded_content"
    storage_retained: Literal[False] = False
    candidates: list[ReviewCandidate] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_page_spans(self) -> Self:
        if self.extracted_chars != len(self.extracted_text):
            raise ValueError("Artifact extracted_chars must match extracted_text length.")
        if not self.page_spans:
            return self
        if self.extraction_method != "pypdf_text":
            raise ValueError("Page spans are only valid for PDF text extraction.")

        expected_page = 1
        expected_start = 0
        for span in self.page_spans:
            if span.page_number != expected_page:
                raise ValueError("PDF page spans must use contiguous one-based page numbers.")
            if span.source_start != expected_start:
                raise ValueError("PDF page spans do not match flattened text boundaries.")
            if span.page_number > 1:
                separator_index = span.source_start - 1
                if self.extracted_text[separator_index] != "\n":
                    raise ValueError("PDF page spans require newline separators between pages.")
            expected_page += 1
            expected_start = span.source_end + 1

        if self.page_spans[-1].source_end != self.extracted_chars:
            raise ValueError("Final PDF page span must end at the extracted text boundary.")
        return self


class FileBatchPreview(BaseModel):
    status: Literal["review_required"] = "review_required"
    artifacts: list[ArtifactPreview] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
