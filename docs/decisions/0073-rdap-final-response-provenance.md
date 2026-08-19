# ADR 0073 — RDAP retains the final response URL as evidence provenance

Status: accepted pre-activation correction

## Context

PersonaLattice already has an IANA-bootstrap-selected RDAP query URL and an SSRF-safe transport that may follow a small number of validated HTTPS redirects. The transport returns both the original canonical query URL and the final URL that returned the RDAP object.

The admission boundary previously required the retained `source_locator` to equal the original bootstrap-derived query URL. That loses information when an authoritative service redirects the request: the retained locator would describe where the request started, not where the evidence was actually returned.

RFC 9224 allows equivalent RDAP services and RDAP deployments may redirect requests. The transport already re-resolves and revalidates every redirect target before I/O.

## Decision

Keep the two URLs distinct:

- `canonical_query_url` is the IANA-bootstrap-derived initial domain query and proves routing authority;
- `source_locator` is the final validated HTTPS URL that actually returned the admitted RDAP object and owns retained evidence provenance.

The admission boundary validates both. The canonical query must still be the exact RFC 9082 `domain/<name>` query for the requested domain. The final source locator must be a canonical HTTPS URL using a DNS hostname, default HTTPS port, no credentials and no fragment. Network-level global-address validation remains the transport's responsibility.

Existing non-redirected callers remain valid because, when `canonical_query_url` is omitted, the source locator is also treated as the canonical query.

## Why this does not activate RDAP

This correction deliberately leaves `rdap_domain_registry` PLANNED, unbound, source-policy-unreviewed and non-recursive. It adds no provider registry entry, shared-runtime owner or RDAP subject request path.

Two activation blockers remain and must not be papered over:

1. the recursive graph has `LeadKind.DOMAIN`, but quick research still has no executable `ResearchKind.DOMAIN` route;
2. IANA bootstrap refresh failure happens before an authoritative RDAP service is contacted and therefore needs an explicit non-attempt source outcome before the provider is activated.

## Privacy and cost

The metadata-only RDAP contract is unchanged. Registrant/contact names, organizations, addresses, email addresses and telephone numbers remain excluded from admitted details. Upstream redaction remains authoritative. No WHOIS fallback, nonpublic registration-data path, paid dependency or credential is added.

## Consequence

A later RDAP adapter can retain honest evidence provenance across redirects without conflating routing authority with the endpoint that actually returned the object. Atomic activation remains blocked until domain execution reachability and bootstrap/non-attempt accounting are both implemented and tested.
