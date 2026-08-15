# SPDX-License-Identifier: Apache-2.0
from enum import Enum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

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
    review_status: ReviewStatus = ReviewStatus.PENDING
    external_research_authorized: bool = False


class ArtifactPreview(BaseModel):
    artifact_id: UUID
    original_name: str
    size_bytes: int
    sha256: str
    detected_media_type: str
    extraction_method: str
    extracted_text: str
    extracted_chars: int
    trust_boundary: Literal["untrusted_document_content"] = "untrusted_document_content"
    storage_retained: Literal[False] = False
    candidates: list[ReviewCandidate] = Field(default_factory=list)


class FileBatchPreview(BaseModel):
    status: Literal["review_required"] = "review_required"
    artifacts: list[ArtifactPreview] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
