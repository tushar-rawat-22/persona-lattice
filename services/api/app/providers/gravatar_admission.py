# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from collections.abc import Mapping
import hashlib
import re
from urllib.parse import urlsplit

_HASH_RE = re.compile(r"^[0-9a-f]{64}$")


class GravatarAdmissionError(ValueError):
    """Fail-closed rejection at the reviewed Gravatar admission boundary."""


def gravatar_profile_identifier(email: str) -> str:
    """Return Gravatar's provider-local SHA-256 identifier for an email.

    Gravatar requires trim + lowercase before hashing. This derivation is local
    to the provider and must not replace PersonaLattice's canonical email
    normalization semantics.
    """

    if not isinstance(email, str):
        raise GravatarAdmissionError("Gravatar email seed must be a string.")
    normalized = email.strip().lower()
    if not normalized or "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
        raise GravatarAdmissionError("Gravatar email seed is malformed.")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _validated_profile_locator(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise GravatarAdmissionError("Gravatar profile requires a public profile_url.")
    parsed = urlsplit(value)
    if parsed.scheme != "https" or parsed.hostname != "gravatar.com":
        raise GravatarAdmissionError("Gravatar profile_url must use https://gravatar.com/.")
    if parsed.username is not None or parsed.password is not None or parsed.port is not None:
        raise GravatarAdmissionError("Gravatar profile_url must not contain credentials or a port.")
    if parsed.query or parsed.fragment:
        raise GravatarAdmissionError("Gravatar profile_url must not contain query or fragment data.")
    slug = parsed.path.strip("/")
    if not slug or "/" in slug or len(slug) > 255:
        raise GravatarAdmissionError("Gravatar profile_url must contain one bounded profile slug.")
    return f"https://gravatar.com/{slug}"


def admitted_gravatar_profile_fields(
    payload: Mapping[str, object],
    *,
    requested_email: str,
) -> tuple[str, dict[str, object]]:
    """Validate one profile response and return minimal retained fields.

    Profile URL is returned separately as canonical provenance. Broader Gravatar
    fields such as location, company, verified accounts, contact information,
    payment data, biography and avatar URLs are intentionally not admitted by
    this pre-activation contract.
    """

    expected_hash = gravatar_profile_identifier(requested_email)
    returned_hash = payload.get("hash")
    if not isinstance(returned_hash, str) or _HASH_RE.fullmatch(returned_hash) is None:
        raise GravatarAdmissionError("Gravatar profile hash is missing or malformed.")
    if returned_hash != expected_hash:
        raise GravatarAdmissionError("Returned Gravatar profile does not match the requested email hash.")

    source_locator = _validated_profile_locator(payload.get("profile_url"))
    details: dict[str, object] = {
        "account_candidate": True,
        "identity_claim": False,
        "field_visibility": "public_profile_api",
    }
    display_name = payload.get("display_name")
    if display_name is not None:
        if not isinstance(display_name, str):
            raise GravatarAdmissionError("Gravatar display_name must be a string when present.")
        if len(display_name) > 512:
            raise GravatarAdmissionError("Gravatar display_name exceeds the admission limit.")
        if display_name:
            details["display_name"] = display_name
    return source_locator, details
