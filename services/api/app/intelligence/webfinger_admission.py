# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from dataclasses import dataclass
import ipaddress
import re
from urllib.parse import urlencode


_ACCOUNT_RE = re.compile(r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]{1,64}$")
_DOMAIN_LABEL_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
_MAX_RESOURCE_CHARS = 320


class WebFingerAdmissionError(ValueError):
    """Raised when an acct resource falls outside the bounded WebFinger contract."""


@dataclass(frozen=True, slots=True)
class WebFingerAcctTarget:
    resource: str
    host: str
    endpoint: str


def _canonical_public_dns_host(value: str) -> str:
    if not value or value.endswith("."):
        raise WebFingerAdmissionError("WebFinger acct domain must be a canonical DNS name.")
    try:
        host = value.encode("idna").decode("ascii").lower()
    except UnicodeError as exc:
        raise WebFingerAdmissionError("WebFinger acct domain is not valid IDNA.") from exc

    if len(host) > 253 or "." not in host:
        raise WebFingerAdmissionError("WebFinger acct domain must be a public-style DNS name.")
    if host == "localhost" or host.endswith(".localhost"):
        raise WebFingerAdmissionError("Local WebFinger targets are not admitted.")
    try:
        ipaddress.ip_address(host.strip("[]"))
    except ValueError:
        pass
    else:
        raise WebFingerAdmissionError("IP-literal WebFinger targets are not admitted.")

    labels = host.split(".")
    if any(not _DOMAIN_LABEL_RE.fullmatch(label) for label in labels):
        raise WebFingerAdmissionError("WebFinger acct domain contains an invalid DNS label.")
    return host


def admit_webfinger_acct_resource(value: str) -> WebFingerAcctTarget:
    """Admit a deliberately small RFC 7033 acct-resource subset without network contact.

    PersonaLattice accepts only an explicit ``acct:local@domain`` resource here.
    This helper does not perform discovery, follow redirects, or claim that the
    account belongs to a person. Runtime WebFinger remains separately governed.
    """

    if not isinstance(value, str) or not value or value != value.strip():
        raise WebFingerAdmissionError("WebFinger resource must be a trimmed non-empty string.")
    if len(value) > _MAX_RESOURCE_CHARS:
        raise WebFingerAdmissionError("WebFinger resource exceeds the local size limit.")
    if any(ord(char) < 0x20 or ord(char) == 0x7F for char in value):
        raise WebFingerAdmissionError("WebFinger resource contains a control character.")
    if not value.startswith("acct:"):
        raise WebFingerAdmissionError("Only explicit acct: WebFinger resources are admitted.")

    account = value[5:]
    if account.count("@") != 1:
        raise WebFingerAdmissionError("WebFinger acct resource must contain one account/domain separator.")
    local, domain = account.split("@", 1)
    if not _ACCOUNT_RE.fullmatch(local):
        raise WebFingerAdmissionError("WebFinger acct local-part is outside the admitted subset.")

    host = _canonical_public_dns_host(domain)
    resource = f"acct:{local}@{host}"
    endpoint = f"https://{host}/.well-known/webfinger?{urlencode({'resource': resource})}"
    return WebFingerAcctTarget(resource=resource, host=host, endpoint=endpoint)
