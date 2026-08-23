# SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass
import ipaddress
import re
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


_DNS_LABEL_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
_MAX_DOMAIN_LENGTH = 253
_LOCAL_USE_DOMAIN_SUFFIXES = (".local", ".localhost", ".internal", ".home", ".lan")
_PUBLIC_WEB_URL_SCHEMES = frozenset({"http", "https"})


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


def _normalize_public_url_hostname(hostname: str) -> str:
    """Return a canonical public DNS hostname for an externally researched URL.

    URL seeds are forwarded to approved public-source providers. Internal hostnames
    and IP literals therefore do not belong at this boundary even when a caller is
    not currently dereferencing the URL directly: forwarding them would disclose
    non-public destination data and would make future URL consumers easier to turn
    into an SSRF path.
    """

    host = hostname.rstrip(".").lower()
    if not host or len(host) > _MAX_DOMAIN_LENGTH:
        raise InvalidIdentifier("URL hostname is missing or too long.")

    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise InvalidIdentifier("Public URL seeds require a DNS hostname, not an IP literal.")

    if "." not in host:
        raise InvalidIdentifier("Public URL seeds require a multi-label DNS hostname.")
    if host.endswith(_LOCAL_USE_DOMAIN_SUFFIXES):
        raise InvalidIdentifier("Public URL seeds must not use a local-use hostname.")

    try:
        ascii_host = host.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise InvalidIdentifier("URL hostname is not valid IDNA.") from exc
    if len(ascii_host) > _MAX_DOMAIN_LENGTH:
        raise InvalidIdentifier("URL hostname is too long after IDNA normalization.")
    if any(_DNS_LABEL_RE.fullmatch(label) is None for label in ascii_host.split(".")):
        raise InvalidIdentifier("URL hostname contains an invalid DNS label.")
    return ascii_host


def _normalize_url(raw: str) -> tuple[str, str]:
    value = raw.strip()
    if not value:
        raise InvalidIdentifier("URL is empty.")
    if any(ord(character) <= 0x20 or ord(character) == 0x7F for character in value):
        raise InvalidIdentifier("URL must not contain whitespace or control characters.")

    candidate = value if "://" in value else f"https://{value}"
    try:
        parsed = urlsplit(candidate)
    except ValueError as exc:
        raise InvalidIdentifier("URL is malformed.") from exc

    scheme = parsed.scheme.lower()
    if scheme not in _PUBLIC_WEB_URL_SCHEMES:
        raise InvalidIdentifier("Public URL seeds must use HTTP or HTTPS.")
    if parsed.username is not None or parsed.password is not None:
        raise InvalidIdentifier("URLs containing embedded credentials are not accepted.")
    if not parsed.hostname:
        raise InvalidIdentifier("URL has no hostname.")

    hostname = _normalize_public_url_hostname(parsed.hostname)

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

    normalized_parts = SplitResult(
        scheme=scheme,
        netloc=netloc,
        path=parsed.path or "",
        query=parsed.query,
        fragment=parsed.fragment,
    )
    normalized = urlunsplit(normalized_parts)
    return normalized, normalized


def _normalize_domain(raw: str) -> tuple[str, str]:
    if any(ord(character) <= 0x20 or ord(character) == 0x7F for character in raw):
        raise InvalidIdentifier("Domain must not contain whitespace or control characters.")
    if "://" in raw or any(character in raw for character in "/?#@"):
        raise InvalidIdentifier("Domain must be a bare DNS name, not a URL or credential-bearing value.")

    domain = raw.rstrip(".").lower()
    if not domain or len(domain) > _MAX_DOMAIN_LENGTH:
        raise InvalidIdentifier("Domain is missing or too long.")
    try:
        ipaddress.ip_address(domain)
    except ValueError:
        pass
    else:
        raise InvalidIdentifier("Domain identifiers do not accept IP literals.")

    if "." not in domain:
        raise InvalidIdentifier("Domain must contain a registrable-style multi-label DNS name.")
    if domain.endswith(_LOCAL_USE_DOMAIN_SUFFIXES):
        raise InvalidIdentifier("Domain must not use a local-use suffix.")
    try:
        ascii_domain = domain.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise InvalidIdentifier("Domain is not valid IDNA.") from exc
    if len(ascii_domain) > _MAX_DOMAIN_LENGTH:
        raise InvalidIdentifier("Domain is too long after IDNA normalization.")
    labels = ascii_domain.split(".")
    if any(_DNS_LABEL_RE.fullmatch(label) is None for label in labels):
        raise InvalidIdentifier("Domain contains an invalid DNS label.")
    return ascii_domain, ascii_domain


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
    elif kind is IdentifierKind.DOMAIN:
        # Domain admission is intentionally stricter than the generic trim-first
        # identifiers: surrounding whitespace is rejected rather than normalized
        # away so URLs, pasted prose and ambiguous values cannot become domains.
        normalized, key = _normalize_domain(raw)
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
