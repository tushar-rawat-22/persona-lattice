# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import ipaddress
import re
from urllib.parse import quote, urlsplit, urlunsplit

_DNS_LABEL_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
_MAX_DOMAIN_LENGTH = 253
_MAX_BOOTSTRAP_SERVICES = 512
_MAX_BASE_URLS_PER_SERVICE = 8
_MAX_STATUS_VALUES = 32
_MAX_NAMESERVERS = 32


class RdapAdmissionError(ValueError):
    """Fail-closed rejection at the reviewed RDAP admission boundary."""


@dataclass(frozen=True, slots=True)
class RdapDomainTarget:
    domain: str
    tld: str


@dataclass(frozen=True, slots=True)
class RdapDomainObservation:
    source_locator: str
    details: dict[str, object]


def normalize_rdap_domain(value: str) -> RdapDomainTarget:
    """Normalize an explicit public DNS domain for future RDAP lookup.

    This is admission-only. It neither discovers subdomains nor performs network
    I/O. IDNs are canonicalized to their ASCII A-label form so bootstrap matching
    and returned-domain validation use one deterministic representation.
    """

    if not isinstance(value, str) or not value:
        raise RdapAdmissionError("RDAP domain must be a non-empty string.")
    if any(ord(character) <= 0x20 or ord(character) == 0x7F for character in value):
        raise RdapAdmissionError("RDAP domain must not contain whitespace or control characters.")
    if "://" in value or any(character in value for character in "/?#@"):
        raise RdapAdmissionError("RDAP domain must be a bare DNS name, not a URL or credential-bearing value.")

    domain = value.rstrip(".").lower()
    if not domain or len(domain) > _MAX_DOMAIN_LENGTH:
        raise RdapAdmissionError("RDAP domain is missing or too long.")
    try:
        ipaddress.ip_address(domain)
    except ValueError:
        pass
    else:
        raise RdapAdmissionError("RDAP domain lookup does not accept IP literals.")

    if "." not in domain:
        raise RdapAdmissionError("RDAP domain must contain a registrable-style multi-label DNS name.")
    if domain.endswith((".local", ".localhost", ".internal", ".home", ".lan")):
        raise RdapAdmissionError("RDAP domain must not use a local-use suffix.")
    try:
        ascii_domain = domain.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise RdapAdmissionError("RDAP domain is not valid IDNA.") from exc
    labels = ascii_domain.split(".")
    if any(_DNS_LABEL_RE.fullmatch(label) is None for label in labels):
        raise RdapAdmissionError("RDAP domain contains an invalid DNS label.")
    return RdapDomainTarget(domain=ascii_domain, tld=labels[-1])


def _validated_bootstrap_base_url(value: str) -> str:
    if not isinstance(value, str) or not value:
        raise RdapAdmissionError("RDAP bootstrap base URL must be a non-empty string.")
    if len(value) > 2048 or any(ord(character) <= 0x20 or ord(character) == 0x7F for character in value):
        raise RdapAdmissionError("RDAP bootstrap base URL is malformed or exceeds limits.")
    parsed = urlsplit(value)
    if parsed.scheme != "https" or parsed.hostname is None:
        raise RdapAdmissionError("RDAP bootstrap base URL must use HTTPS.")
    if parsed.username is not None or parsed.password is not None:
        raise RdapAdmissionError("RDAP bootstrap base URL must not contain credentials.")
    if parsed.query or parsed.fragment:
        raise RdapAdmissionError("RDAP bootstrap base URL must not contain query or fragment data.")
    try:
        port = parsed.port
    except ValueError as exc:
        raise RdapAdmissionError("RDAP bootstrap base URL has an invalid port.") from exc
    if port not in {None, 443}:
        raise RdapAdmissionError("RDAP bootstrap base URL may use only the default HTTPS port.")
    hostname = parsed.hostname.rstrip(".").lower()
    try:
        ipaddress.ip_address(hostname)
    except ValueError:
        pass
    else:
        raise RdapAdmissionError("RDAP bootstrap base URL must use a DNS hostname.")
    try:
        hostname = hostname.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise RdapAdmissionError("RDAP bootstrap hostname is not valid IDNA.") from exc
    if "." not in hostname or any(_DNS_LABEL_RE.fullmatch(label) is None for label in hostname.split(".")):
        raise RdapAdmissionError("RDAP bootstrap hostname is not a valid public DNS-style hostname.")
    path = parsed.path or "/"
    if not path.endswith("/"):
        path += "/"
    return urlunsplit(("https", hostname, path, "", ""))


def _normalized_bootstrap_suffix(value: str) -> str:
    if not isinstance(value, str) or not value:
        raise RdapAdmissionError("RDAP bootstrap DNS entries must be non-empty strings.")
    if any(ord(character) <= 0x20 or ord(character) == 0x7F for character in value):
        raise RdapAdmissionError("RDAP bootstrap DNS entry is malformed.")
    suffix = value.rstrip(".").lower()
    try:
        suffix = suffix.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise RdapAdmissionError("RDAP bootstrap DNS entry is not valid IDNA.") from exc
    labels = suffix.split(".")
    if not labels or any(_DNS_LABEL_RE.fullmatch(label) is None for label in labels):
        raise RdapAdmissionError("RDAP bootstrap DNS entry contains an invalid label.")
    return suffix


def _bootstrap_suffix_matches(domain: str, suffix: str) -> bool:
    return domain == suffix or domain.endswith(f".{suffix}")


def rdap_bootstrap_base_urls(payload: Mapping[str, object], *, domain: str) -> tuple[str, ...]:
    """Resolve one domain to authoritative HTTPS base URLs from IANA-style bootstrap data.

    RFC 9224 requires DNS bootstrap selection by the longest matching label suffix,
    not merely by the final TLD. Equivalent entries at the same longest match are
    combined in registry order; less-specific matches are ignored.
    """

    target = normalize_rdap_domain(domain)
    services = payload.get("services")
    if not isinstance(services, Sequence) or isinstance(services, (str, bytes)):
        raise RdapAdmissionError("RDAP bootstrap payload requires a services array.")
    if len(services) > _MAX_BOOTSTRAP_SERVICES:
        raise RdapAdmissionError("RDAP bootstrap payload exceeds the service admission limit.")

    longest_label_count = 0
    matching_url_groups: list[Sequence[object]] = []
    for service in services:
        if not isinstance(service, Sequence) or isinstance(service, (str, bytes)) or len(service) != 2:
            raise RdapAdmissionError("RDAP bootstrap service entries must contain DNS and URL arrays.")
        suffixes, urls = service
        if not isinstance(suffixes, Sequence) or isinstance(suffixes, (str, bytes)):
            raise RdapAdmissionError("RDAP bootstrap DNS list must be an array.")
        if not isinstance(urls, Sequence) or isinstance(urls, (str, bytes)):
            raise RdapAdmissionError("RDAP bootstrap URL list must be an array.")
        if len(urls) > _MAX_BASE_URLS_PER_SERVICE:
            raise RdapAdmissionError("RDAP bootstrap service exposes too many base URLs.")

        service_match_length = 0
        for raw_suffix in suffixes:
            suffix = _normalized_bootstrap_suffix(raw_suffix)
            if _bootstrap_suffix_matches(target.domain, suffix):
                service_match_length = max(service_match_length, suffix.count(".") + 1)
        if service_match_length == 0:
            continue
        if service_match_length > longest_label_count:
            longest_label_count = service_match_length
            matching_url_groups = [urls]
        elif service_match_length == longest_label_count:
            matching_url_groups.append(urls)

    matches: list[str] = []
    for urls in matching_url_groups:
        for url in urls:
            normalized_url = _validated_bootstrap_base_url(url)
            if normalized_url not in matches:
                matches.append(normalized_url)

    if not matches:
        raise RdapAdmissionError("RDAP bootstrap payload has no authoritative service for the domain.")
    return tuple(matches)


def rdap_domain_query_url(base_url: str, *, domain: str) -> str:
    """Construct a bounded RFC 9082 domain query URL from an admitted bootstrap base URL."""

    target = normalize_rdap_domain(domain)
    base = _validated_bootstrap_base_url(base_url)
    return f"{base}domain/{quote(target.domain, safe='.-')}"


def admitted_rdap_domain_observation(
    payload: Mapping[str, object],
    *,
    requested_domain: str,
    source_locator: str,
) -> RdapDomainObservation:
    """Retain only low-sensitivity public registration context from a domain response.

    Registrant/contact names, addresses, email, telephone and organization values
    are intentionally excluded even when an upstream response exposes them. The
    authoritative service's redaction remains authoritative; this boundary never
    attempts to infer or recover omitted registration data.
    """

    target = normalize_rdap_domain(requested_domain)
    if payload.get("objectClassName") != "domain":
        raise RdapAdmissionError("RDAP response must be a domain object.")
    ldh_name = payload.get("ldhName")
    if not isinstance(ldh_name, str):
        raise RdapAdmissionError("RDAP domain response requires ldhName.")
    returned = normalize_rdap_domain(ldh_name).domain
    if returned != target.domain:
        raise RdapAdmissionError("RDAP response domain does not match the requested domain.")

    expected_locator = rdap_domain_query_url(source_locator.rsplit("domain/", 1)[0], domain=target.domain)
    if source_locator != expected_locator:
        raise RdapAdmissionError("RDAP source locator is not the canonical admitted domain query URL.")

    statuses = payload.get("status", ())
    if not isinstance(statuses, Sequence) or isinstance(statuses, (str, bytes)):
        raise RdapAdmissionError("RDAP domain status must be an array when present.")
    if len(statuses) > _MAX_STATUS_VALUES or any(not isinstance(item, str) for item in statuses):
        raise RdapAdmissionError("RDAP domain status exceeds limits or contains non-string values.")

    nameservers = payload.get("nameservers", ())
    if not isinstance(nameservers, Sequence) or isinstance(nameservers, (str, bytes)):
        raise RdapAdmissionError("RDAP nameservers must be an array when present.")
    if len(nameservers) > _MAX_NAMESERVERS:
        raise RdapAdmissionError("RDAP domain response exposes too many nameservers.")
    admitted_nameservers: list[str] = []
    for item in nameservers:
        if not isinstance(item, Mapping):
            raise RdapAdmissionError("RDAP nameserver entries must be objects.")
        name = item.get("ldhName")
        if not isinstance(name, str):
            raise RdapAdmissionError("RDAP nameserver entry requires ldhName.")
        normalized = normalize_rdap_domain(name).domain
        if normalized not in admitted_nameservers:
            admitted_nameservers.append(normalized)

    details: dict[str, object] = {
        "domain": target.domain,
        "statuses": tuple(statuses),
        "nameservers": tuple(admitted_nameservers),
        "registration_context": True,
        "identity_claim": False,
        "registrant_contact_retained": False,
        "redaction_authoritative": True,
    }
    return RdapDomainObservation(source_locator=source_locator, details=details)
