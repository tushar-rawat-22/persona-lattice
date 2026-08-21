# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import re
from urllib.parse import unquote, urlsplit


MAX_DOI_LENGTH = 512
_DOI_RE = re.compile(r"^10\.[0-9]{4,9}/\S+$", re.IGNORECASE)
_HEX = frozenset("0123456789abcdefABCDEF")


def _has_valid_percent_encoding(value: str) -> bool:
    index = 0
    while index < len(value):
        if value[index] != "%":
            index += 1
            continue
        if index + 2 >= len(value) or value[index + 1] not in _HEX or value[index + 2] not in _HEX:
            return False
        index += 3
    return True


def validated_doi(value: str) -> str | None:
    """Return one bounded printable DOI or ``None`` for unsupported input."""

    if not value or len(value) > MAX_DOI_LENGTH:
        return None
    if any(ord(character) < 0x21 or ord(character) > 0x7E for character in value):
        return None
    if _DOI_RE.fullmatch(value) is None:
        return None
    return value


def doi_from_canonical_url(value: str) -> str | None:
    """Return the DOI carried by an exact canonical ``https://doi.org/...`` URL."""

    try:
        parts = urlsplit(value)
        port = parts.port
    except ValueError:
        return None
    if (
        parts.scheme != "https"
        or parts.hostname is None
        or parts.hostname.casefold() != "doi.org"
        or parts.username is not None
        or parts.password is not None
        or port is not None
        or parts.query
        or parts.fragment
        or not parts.path.startswith("/")
        or parts.path == "/"
    ):
        return None

    encoded = parts.path[1:]
    if not _has_valid_percent_encoding(encoded):
        return None
    try:
        doi = unquote(encoded, encoding="utf-8", errors="strict")
    except UnicodeDecodeError:
        return None
    return validated_doi(doi)
