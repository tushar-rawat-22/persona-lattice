# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import ipaddress
import re
from urllib.parse import quote, urlsplit, urlunsplit

_DNS_LABEL_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")


class WebFingerAdmissionError(ValueError):
    """Fail-closed rejection at the reviewed WebFinger admission boundary."""


@dataclass(frozen=True, slots=True)
class WebFingerRequestTarget:
    resource: str
    hostname: str
    endpoint: str


@dataclass(frozen=True, slots=True)
class WebFingerNetworkTarget:
    """Validated HTTPS target that still requires fresh DNS admission before I/O."""

    url: str
    hostname: str
    request_target: str


def _require_clean_url(value: str, *, label: str) -> None:
    if not isinstance(value, str) or not value:
        raise WebFingerAdmissionError(f"{label} must be a non-empty string.")
    if len(value) > 2048:
        raise WebFingerAdmissionError(f"{label} exceeds the admission limit.")
    if any(ord(character) <= 0x20 or ord(character) == 0x7F for character in value):
        raise WebFingerAdmissionError(f"{label} must not contain whitespace or control characters.")


def _admitted_dns_hostname(hostname: str) -> str:
    """Validate a DNS-style hostname without claiming current routability.

    A future network adapter must still resolve and reject non-global addresses
    immediately before I/O and after every redirect.
    """

    value = hostname.rstrip(".").lower()
    if not value or len(value) > 253:
        raise WebFingerAdmissionError("WebFinger profile URL hostname is missing or too long.")
    try:
        ipaddress.ip_address(value)
    except ValueError:
        pass
    else:
        raise WebFingerAdmissionError("WebFinger profile URL must use a DNS hostname, not an IP literal.")

    if "." not in value:
        raise WebFingerAdmissionError("WebFinger profile URL must use a multi-label DNS hostname.")
    if value.endswith((".local", ".localhost", ".internal", ".home", ".lan")):
        raise WebFingerAdmissionError("WebFinger profile URL must not target a local-use hostname.")
    try:
        ascii_value = value.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise WebFingerAdmissionError("WebFinger profile URL hostname is not valid IDNA.") from exc
    labels = ascii_value.split(".")
    if any(_DNS_LABEL_RE.fullmatch(label) is None for label in labels):
        raise WebFingerAdmissionError("WebFinger profile URL hostname has an invalid DNS label.")
    return ascii_value


def webfinger_network_target(url: str, *, allow_query: bool) -> WebFingerNetworkTarget:
    """Validate one HTTPS network target without performing DNS or network I/O.

    Redirect service URIs may carry a query string under RFC 7033, while profile
    seeds and admitted evidence links remain query-free. Every returned hostname
    still needs fresh global-address resolution before a connection is opened.
    """

    _require_clean_url(url, label="WebFinger network target")
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname is None:
        raise WebFingerAdmissionError("WebFinger network target must be an absolute HTTPS URL.")
    if parsed.username is not None or parsed.password is not None or parsed.port is not None:
        raise WebFingerAdmissionError("WebFinger network target must not contain credentials or an explicit port.")
    if parsed.fragment:
        raise WebFingerAdmissionError("WebFinger network target must not contain a fragment.")
    if parsed.query and not allow_query:
        raise WebFingerAdmissionError("WebFinger network target must not contain query data here.")

    hostname = _admitted_dns_hostname(parsed.hostname)
    path = parsed.path or "/"
    normalized = urlunsplit(("https", hostname, path, parsed.query, ""))
    request_target = path + (f"?{parsed.query}" if parsed.query else "")
    return WebFingerNetworkTarget(
        url=normalized,
        hostname=hostname,
        request_target=request_target,
    )


def webfinger_request_target(profile_url: str) -> WebFingerRequestTarget:
    """Build a bounded RFC 7033 request target from an explicit HTTPS profile URL.

    This is admission-only. It performs no DNS resolution or network request.
    """

    _require_clean_url(profile_url, label="WebFinger profile URL")
    parsed = urlsplit(profile_url)
    if parsed.scheme != "https" or parsed.hostname is None:
        raise WebFingerAdmissionError("WebFinger profile URL must be an absolute HTTPS URL.")
    if parsed.username is not None or parsed.password is not None or parsed.port is not None:
        raise WebFingerAdmissionError("WebFinger profile URL must not contain credentials or an explicit port.")
    if parsed.query or parsed.fragment:
        raise WebFingerAdmissionError("WebFinger profile URL must not contain query or fragment data.")
    if not parsed.path or parsed.path == "/":
        raise WebFingerAdmissionError("WebFinger profile URL must identify a concrete profile resource.")
    if parsed.path.startswith("/.well-known/"):
        raise WebFingerAdmissionError("WebFinger profile URL must not point at a well-known endpoint.")

    hostname = _admitted_dns_hostname(parsed.hostname)
    resource = urlunsplit(("https", hostname, parsed.path, "", ""))
    endpoint = f"https://{hostname}/.well-known/webfinger?resource={quote(resource, safe='')}"
    return WebFingerRequestTarget(resource=resource, hostname=hostname, endpoint=endpoint)


def admitted_webfinger_links(
    payload: Mapping[str, object],
    *,
    requested_resource: str,
) -> tuple[str, ...]:
    """Return only bounded HTTPS links from a JRD tied to the requested resource.

    WebFinger itself does not establish display names or a safe generic username
    lead. ActivityPub actor fetching is deliberately outside this preflight.
    """

    target = webfinger_request_target(requested_resource)
    subject = payload.get("subject")
    aliases = payload.get("aliases", ())
    if not isinstance(subject, str):
        raise WebFingerAdmissionError("WebFinger JRD requires a string subject.")
    if not isinstance(aliases, Sequence) or isinstance(aliases, (str, bytes)):
        raise WebFingerAdmissionError("WebFinger JRD aliases must be an array when present.")
    alias_values = tuple(alias for alias in aliases if isinstance(alias, str))
    if len(alias_values) != len(aliases):
        raise WebFingerAdmissionError("WebFinger JRD aliases must contain strings only.")
    if target.resource != subject and target.resource not in alias_values:
        raise WebFingerAdmissionError("WebFinger JRD is not anchored to the requested profile URL.")

    links = payload.get("links", ())
    if not isinstance(links, Sequence) or isinstance(links, (str, bytes)):
        raise WebFingerAdmissionError("WebFinger JRD links must be an array when present.")
    if len(links) > 32:
        raise WebFingerAdmissionError("WebFinger JRD exceeds the link admission limit.")

    admitted: list[str] = []
    for item in links:
        if not isinstance(item, Mapping):
            raise WebFingerAdmissionError("WebFinger JRD link entries must be objects.")
        rel = item.get("rel")
        href = item.get("href")
        if rel not in {"self", "http://webfinger.net/rel/profile-page"} or href is None:
            continue
        if not isinstance(href, str):
            raise WebFingerAdmissionError("WebFinger admitted href must be a string.")
        target_link = webfinger_network_target(href, allow_query=False)
        if target_link.url not in admitted:
            admitted.append(target_link.url)
    return tuple(admitted)
