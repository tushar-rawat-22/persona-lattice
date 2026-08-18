# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Literal

_HANDLE_RE = re.compile(
    r"^([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"[a-z]([a-z0-9-]{0,61}[a-z0-9])?$"
)
_DISALLOWED_REAL_WORLD_TLDS = frozenset(
    {"alt", "arpa", "example", "internal", "invalid", "local", "localhost", "onion", "test"}
)


class BlueskyAdmissionError(ValueError):
    """Local fail-closed rejection before any Bluesky network call."""


def normalize_bluesky_handle(value: str) -> str:
    """Return a real-world AT Protocol handle or reject it before execution.

    PersonaLattice's generic username lead kind is broader than an AT Protocol
    handle. This guard prevents ordinary usernames from turning into speculative
    Bluesky requests.
    """

    if not isinstance(value, str):
        raise BlueskyAdmissionError("Bluesky handle must be a string.")
    normalized = value.lower()
    if value != value.strip() or normalized.startswith("@"):
        raise BlueskyAdmissionError("Bluesky handle must use backend handle syntax without @.")
    if len(normalized) > 253 or _HANDLE_RE.fullmatch(normalized) is None:
        raise BlueskyAdmissionError("Value is not a syntactically valid AT Protocol handle.")
    tld = normalized.rsplit(".", 1)[1]
    if tld in _DISALLOWED_REAL_WORLD_TLDS:
        raise BlueskyAdmissionError("Reserved or non-public handle TLD is not executable.")
    return normalized


def bluesky_public_web_visibility(
    payload: Mapping[str, object],
) -> Literal["allowed", "opted_out"]:
    """Resolve the public-web visibility decision from returned profile labels.

    A malformed labels structure is rejected rather than treated as absence of an
    opt-out signal. The network adapter will map ``opted_out`` to a typed attempted
    source outcome instead of pretending the account was not found.
    """

    labels = payload.get("labels")
    if labels is None:
        return "allowed"
    if not isinstance(labels, list):
        raise BlueskyAdmissionError("Bluesky profile labels must be an array when present.")
    for item in labels:
        if not isinstance(item, Mapping):
            raise BlueskyAdmissionError("Bluesky profile label entries must be objects.")
        value = item.get("val")
        if not isinstance(value, str) or not value:
            raise BlueskyAdmissionError("Bluesky profile labels require a non-empty val field.")
        if value == "!no-unauthenticated":
            return "opted_out"
    return "allowed"


def admitted_bluesky_profile_fields(
    payload: Mapping[str, object],
    *,
    requested_handle: str,
) -> dict[str, object]:
    """Return the minimal reviewed profile field set after local admission checks."""

    handle = payload.get("handle")
    did = payload.get("did")
    if not isinstance(handle, str) or not isinstance(did, str):
        raise BlueskyAdmissionError("Bluesky profile requires string handle and DID fields.")
    normalized_requested = normalize_bluesky_handle(requested_handle)
    normalized_returned = normalize_bluesky_handle(handle)
    if normalized_returned != normalized_requested:
        raise BlueskyAdmissionError("Returned Bluesky handle does not match the requested handle.")
    if not did.startswith("did:") or len(did) > 2048:
        raise BlueskyAdmissionError("Returned Bluesky DID is malformed.")
    if bluesky_public_web_visibility(payload) != "allowed":
        raise BlueskyAdmissionError("Bluesky profile opted out of unauthenticated public-web use.")

    result: dict[str, object] = {
        "did": did,
        "handle": normalized_returned,
        "account_candidate": True,
        "identity_claim": False,
        "field_visibility": "public_profile_api",
        "public_web_visibility": "allowed",
    }
    display_name = payload.get("displayName")
    if display_name is not None:
        if not isinstance(display_name, str):
            raise BlueskyAdmissionError("Bluesky displayName must be a string when present.")
        if display_name:
            result["display_name"] = display_name
    return result
