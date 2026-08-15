# SPDX-License-Identifier: Apache-2.0
from fastapi import HTTPException, status

from .models import Purpose


BLOCKED = {
    Purpose.EMPLOYMENT_DECISION: (
        "Employment eligibility decisions are outside the bootstrap product scope."
    ),
    Purpose.HOUSING_DECISION: (
        "Housing eligibility decisions are outside the bootstrap product scope."
    ),
    Purpose.CREDIT_DECISION: (
        "Credit eligibility decisions are outside the bootstrap product scope."
    ),
    Purpose.INSURANCE_DECISION: (
        "Insurance eligibility decisions are outside the bootstrap product scope."
    ),
}


def enforce_purpose(purpose: Purpose, consent_acknowledged: bool) -> None:
    if purpose in BLOCKED:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=BLOCKED[purpose],
        )

    if purpose in {
        Purpose.SELF_AUDIT,
        Purpose.CONSENTED_DUE_DILIGENCE,
        Purpose.PROFESSIONAL_VERIFICATION,
    } and not consent_acknowledged:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="This purpose requires the consent/authorization acknowledgement.",
        )
