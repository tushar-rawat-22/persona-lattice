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
    trust_boundary: Literal["untrusted_uploaded_content"] = "untrusted_uploaded_content"
    storage_retained: Literal[False] = False
    candidates: list[ReviewCandidate] = Field(default_factory=list)


class FileBatchPreview(BaseModel):
    status: Literal["review_required"] = "review_required"
    artifacts: list[ArtifactPreview] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
