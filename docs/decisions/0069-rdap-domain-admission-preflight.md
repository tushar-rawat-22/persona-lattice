# ADR 0069 — RDAP domain admission stays metadata-only before activation

Status: accepted for pre-activation review

## Context

WebFinger remains non-executable because no concrete host has yet passed the exact-host source-policy gate. The next zero-spend source candidate is domain RDAP.

Current primary material supports RDAP as the authoritative standardized path for current domain registration data. IANA publishes the DNS bootstrap registry used to locate authoritative RDAP services, RFC 9082 defines the `/domain/<name>` query form, and ICANN treats RDAP as the definitive gTLD registration-data service. RDAP also supports differentiated access and privacy redaction; nonpublic registration data is outside PersonaLattice's public baseline.

The existing catalog entry for `rdap_domain_registry` claimed that a domain lookup could emit an `ORGANIZATION` lead. That claim is not safe enough for activation. A registrar organization identifies the registration service, not necessarily the investigated subject. A registrant organization may be redacted and, when published, still requires careful role interpretation. It must not become an automatic subject-organization pivot merely because RDAP returned it.

## Decision

Add a network-free RDAP admission boundary before any adapter or provider activation.

The preflight:

- accepts only explicit bare multi-label DNS domain names;
- canonicalizes IDNs to ASCII A-label form;
- rejects URLs, credentials, IP literals and local-use names;
- reads only IANA-style DNS bootstrap service entries matching the domain TLD;
- accepts HTTPS bootstrap base URLs only and rejects credentials, query/fragment data and non-default ports;
- constructs the RFC 9082 `domain/<name>` query path deterministically;
- requires a returned RDAP object to be a domain object whose `ldhName` matches the requested domain;
- retains only bounded domain status and nameserver context plus explicit non-identity/redaction metadata;
- ignores registrant/contact names, addresses, email, telephone and organization values even when upstream returns them;
- never attempts to infer, recover or request data that the authoritative RDAP service redacts.

`rdap_domain_registry` remains `PLANNED`, unbound and non-recursive in this block. No RDAP network request is added.

## Catalog correction required before activation

The current `ORGANIZATION` emission declaration is a known blocker. RDAP activation must first narrow the source to metadata-only output (`emits = ∅`) unless a later, separately reviewed semantic contract proves a specific organization field is an attributable lead rather than registry/registrar context.

Keeping the source planned while this overclaim remains is intentional fail-closed behavior.

## Transport still required

Admission of a bootstrap URL does not prove a safe network target at request time. A future adapter must still use bounded HTTPS transport with fresh DNS/global-address validation and fail-closed redirect handling comparable to the existing WebFinger SSRF boundary. It must also distinguish not-found, malformed response, remote rate limit and transient unavailability through the typed source-run contract.

## Cost and privacy

This preflight adds no credential or paid dependency. ICANN describes RDAP clients as publicly available and free to use, while authoritative services may apply access controls or rate limits. PersonaLattice will use only data actually returned to an unauthenticated public request and will treat redaction as authoritative.

No nonpublic-registration-data request workflow, RDRS integration, WHOIS fallback, bulk search, reverse search or contact harvesting is approved by this decision.

## Next gate

Correct the catalog emission overclaim, then implement one bounded RDAP transport/provider block using the IANA DNS bootstrap registry and the existing governed `ProviderRuntime`. Activation must remain metadata-only and zero-spend.
