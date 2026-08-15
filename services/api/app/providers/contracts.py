# SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass
from enum import Enum
from uuid import UUID

from ..models import Purpose
from ..uploads import ReviewCandidate


class QueryOrigin(str, Enum):
    USER_SUPPLIED = "user_supplied"
    CONFIRMED_DOCUMENT_CANDIDATE = "confirmed_document_candidate"


@dataclass(frozen=True, slots=True)
class ExecutionRequest:
    provider_name: str
    subject_id: UUID
    identifier_id: UUID
    purpose: Purpose
    consent_acknowledged: bool
    query_origin: QueryOrigin = QueryOrigin.USER_SUPPLIED
    document_candidate: ReviewCandidate | None = None
    silent_mode: bool = True
