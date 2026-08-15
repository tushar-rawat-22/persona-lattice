# SPDX-License-Identifier: Apache-2.0
import re

import phonenumbers

from .normalization import NormalizedIdentifier
from .types import IdentifierKind

REDACTED_PHONE = "[REDACTED_PHONE]"
REDACTED_EMAIL = "[REDACTED_EMAIL]"
REDACTED_USERNAME = "[REDACTED_USERNAME]"


def _phone_variants(value: str) -> set[str]:
    variants = {value, "".join(character for character in value if character.isdigit())}

    try:
        parsed = phonenumbers.parse(value, None)
    except phonenumbers.NumberParseException:
        return {item for item in variants if item}

    for style in (
        phonenumbers.PhoneNumberFormat.E164,
        phonenumbers.PhoneNumberFormat.INTERNATIONAL,
        phonenumbers.PhoneNumberFormat.NATIONAL,
    ):
        variants.add(phonenumbers.format_number(parsed, style))

    national = str(parsed.national_number)
    variants.add(national)
    variants.add(f"0{national}")

    if len(national) == 10:
        variants.add(f"{national[:5]} {national[5:]}")
        variants.add(f"0{national[:5]} {national[5:]}")

    return {item for item in variants if item}


def redact_text(text: str, identifiers: list[NormalizedIdentifier]) -> str:
    redacted = text

    for identifier in identifiers:
        if identifier.kind is IdentifierKind.EMAIL:
            variants = {
                identifier.raw_value.strip(),
                identifier.normalized_value,
            }
            for variant in sorted(variants, key=len, reverse=True):
                if variant:
                    redacted = re.sub(
                        re.escape(variant),
                        REDACTED_EMAIL,
                        redacted,
                        flags=re.IGNORECASE,
                    )

        elif identifier.kind is IdentifierKind.PHONE:
            for variant in sorted(
                _phone_variants(identifier.normalized_value),
                key=len,
                reverse=True,
            ):
                redacted = redacted.replace(variant, REDACTED_PHONE)

        elif identifier.kind is IdentifierKind.USERNAME:
            variants = {
                identifier.raw_value.strip(),
                identifier.normalized_value,
            }
            for variant in sorted(variants, key=len, reverse=True):
                if not variant:
                    continue
                redacted = re.sub(
                    rf"(?<![A-Za-z0-9_.-]){re.escape(variant)}(?![A-Za-z0-9_.-])",
                    REDACTED_USERNAME,
                    redacted,
                )

    return redacted
