# SPDX-License-Identifier: Apache-2.0
from ..models import Purpose
from ..uploads import (
    CandidateReviewError,
    CandidateType,
    require_research_authorization,
)
from .base import ContactRisk, ProviderDescriptor, ProviderStatus
from .contracts import ExecutionRequest, QueryOrigin
from .errors import ProviderPolicyError


REGULATED_PURPOSES = {
    Purpose.EMPLOYMENT_DECISION,
    Purpose.HOUSING_DECISION,
    Purpose.CREDIT_DECISION,
    Purpose.INSURANCE_DECISION,
}
CONSENT_REQUIRED = {
    Purpose.SELF_AUDIT,
    Purpose.CONSENTED_DUE_DILIGENCE,
    Purpose.PROFESSIONAL_VERIFICATION,
}
EXECUTABLE_STATUSES = {
    ProviderStatus.SYNTHETIC.value,
    ProviderStatus.DEVELOPMENT.value,
}


def authorize_execution(descriptor: ProviderDescriptor, request: ExecutionRequest) -> None:
    if request.purpose in REGULATED_PURPOSES:
        raise ProviderPolicyError("Regulated eligibility purposes are blocked.")
    if request.purpose in CONSENT_REQUIRED and not request.consent_acknowledged:
        raise ProviderPolicyError("This purpose requires consent or authorization acknowledgement.")
    if request.purpose not in descriptor.allowed_purposes:
        raise ProviderPolicyError("This provider is not allowed for the requested purpose.")
    if descriptor.status not in EXECUTABLE_STATUSES:
        raise ProviderPolicyError("This provider has not been approved for execution.")
    if request.silent_mode and descriptor.contact_risk is not ContactRisk.NONE_KNOWN:
        raise ProviderPolicyError("Silent execution cannot use a provider with subject-contact risk.")

    if request.query_origin is QueryOrigin.CONFIRMED_DOCUMENT_CANDIDATE:
        candidate = request.document_candidate
        if candidate is None:
            raise ProviderPolicyError("Document-derived queries require their review candidate.")
        if candidate.candidate_type is not CandidateType.IDENTIFIER:
            raise ProviderPolicyError("Only confirmed identifier candidates can be queried.")
        try:
            require_research_authorization(candidate)
        except CandidateReviewError as exc:
            raise ProviderPolicyError("Document-derived candidate is not authorized for research.") from exc
    elif request.document_candidate is not None:
        raise ProviderPolicyError("A document candidate must use the document-candidate query origin.")
