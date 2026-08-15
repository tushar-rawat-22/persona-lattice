# SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass
from urllib.parse import SplitResult, urlsplit, urlunsplit

import phonenumbers

from .types import IdentifierKind


class InvalidIdentifier(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class NormalizedIdentifier:
    kind: IdentifierKind
    raw_value: str
    normalized_value: str
    comparison_key: str


def _compact_whitespace(value: str) -> str:
    return " ".join(value.split())


def _normalize_phone(raw: str) -> tuple[str, str]:
    try:
        parsed = phonenumbers.parse(raw, None)
    except phonenumbers.NumberParseException as exc:
        raise InvalidIdentifier("Phone could not be parsed.") from exc

    if not phonenumbers.is_possible_number(parsed):
        raise InvalidIdentifier("Phone is not recognized as a possible number.")

    value = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    return value, value


def _normalize_email(raw: str) -> tuple[str, str]:
    value = raw.strip()
    if value.count("@") != 1 or any(character.isspace() for character in value):
        raise InvalidIdentifier("Email is malformed.")

    local, domain = value.rsplit("@", 1)
    if not local or not domain or "." not in domain:
        raise InvalidIdentifier("Email is malformed.")

    normalized = f"{local}@{domain.lower()}"
    return normalized, normalized


def _normalize_username(raw: str) -> tuple[str, str]:
    value = raw.strip().lstrip("@").strip()
    if not value or any(character.isspace() for character in value):
        raise InvalidIdentifier("Username is malformed.")
    return value, value


def _normalize_url(raw: str) -> tuple[str, str]:
    value = raw.strip()
    if not value:
        raise InvalidIdentifier("URL is empty.")

    candidate = value if "://" in value else f"https://{value}"
    parsed = urlsplit(candidate)

    if not parsed.hostname:
        raise InvalidIdentifier("URL has no hostname.")

    scheme = parsed.scheme.lower()
    hostname = parsed.hostname.lower()

    try:
        port = parsed.port
    except ValueError as exc:
        raise InvalidIdentifier("URL contains an invalid port.") from exc

    if port is not None and not (
        (scheme == "https" and port == 443) or (scheme == "http" and port == 80)
    ):
        netloc = f"{hostname}:{port}"
    else:
        netloc = hostname

    if parsed.username or parsed.password:
        raise InvalidIdentifier("URLs containing embedded credentials are not accepted.")

    normalized_parts = SplitResult(
        scheme=scheme,
        netloc=netloc,
        path=parsed.path or "",
        query=parsed.query,
        fragment=parsed.fragment,
    )
    normalized = urlunsplit(normalized_parts)
    return normalized, normalized


def normalize_identifier(kind: IdentifierKind, raw: str) -> NormalizedIdentifier:
    raw_value = raw.strip()

    if not raw_value:
        raise InvalidIdentifier(f"{kind.value} is empty.")

    if kind is IdentifierKind.PHONE:
        normalized, key = _normalize_phone(raw_value)
    elif kind is IdentifierKind.EMAIL:
        normalized, key = _normalize_email(raw_value)
    elif kind is IdentifierKind.USERNAME:
        normalized, key = _normalize_username(raw_value)
    elif kind is IdentifierKind.URL:
        normalized, key = _normalize_url(raw_value)
    elif kind in {IdentifierKind.NAME, IdentifierKind.ORGANIZATION}:
        normalized = _compact_whitespace(raw_value)
        key = normalized.casefold()
    else:
        raise InvalidIdentifier(f"Unsupported identifier kind: {kind!r}")

    return NormalizedIdentifier(
        kind=kind,
        raw_value=raw,
        normalized_value=normalized,
        comparison_key=key,
    )


def normalize_collection(
    kind: IdentifierKind,
    values: list[str],
) -> tuple[list[NormalizedIdentifier], list[str]]:
    normalized: dict[str, NormalizedIdentifier] = {}
    warnings: list[str] = []

    for raw in values:
        try:
            item = normalize_identifier(kind, raw)
        except InvalidIdentifier as exc:
            warnings.append(f"{raw}: {exc}")
            continue
        normalized.setdefault(item.comparison_key, item)

    ordered = sorted(normalized.values(), key=lambda item: item.comparison_key)
    return ordered, warnings
