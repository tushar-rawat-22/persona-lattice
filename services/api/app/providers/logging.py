# SPDX-License-Identifier: Apache-2.0
from collections.abc import Iterable

from ..evidence import NormalizedIdentifier, redact_text


REDACTED_SECRET = "[REDACTED_SECRET]"


def sanitize_provider_log(
    message: str,
    *,
    identifiers: list[NormalizedIdentifier] | None = None,
    secrets: Iterable[str] = (),
) -> str:
    redacted = redact_text(message, identifiers or [])
    for secret in sorted({value for value in secrets if value}, key=len, reverse=True):
        redacted = redacted.replace(secret, REDACTED_SECRET)
    return redacted
