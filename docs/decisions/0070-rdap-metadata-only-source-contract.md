# ADR 0070 — RDAP domain metadata does not emit subject leads

Status: accepted for pre-activation review

## Context

ADR 0069 established a network-free RDAP admission boundary and found one catalog overclaim: `rdap_domain_registry` was declared to emit `ORGANIZATION` leads.

That declaration was not defensible. A registrar organization describes the registration service, not the researched subject. A registrant organization can be redacted and, even when public, still needs role and attribution review before it could be treated as subject evidence. Automatic organization emission would therefore turn registration context into a subject pivot without sufficient semantics.

The RDAP admission layer already retains only bounded domain status and nameserver context and drops registrant/contact names, organizations, addresses, email addresses and telephone numbers.

## Decision

Make the planned RDAP source metadata-only:

- `rdap_domain_registry.emits = frozenset()`;
- keep the source `PLANNED`, source-policy-unreviewed, unbound and non-recursive;
- keep admitted RDAP observations limited to domain/status/nameserver registration context plus non-identity/redaction flags;
- regression-test the retained observation through the normal exact-field lead extractor and require zero typed lead candidates;
- continue to treat upstream privacy redaction as authoritative.

This closes Issue #124 but does not authorize RDAP execution.

## Consequences

RDAP can provide useful context about a domain without creating automatic person or organization pivots. Registrar/registrant/contact data cannot enter the recursive lead graph through this source contract.

If a future use case needs an organization field from registration data, it requires a separate semantic review that identifies the role, attribution basis, retention need and lead disposition. It must not be reintroduced as a generic RDAP organization field.

## Still required before activation

A later block must implement and review the authoritative RDAP transport/provider path:

- resolve the service from the IANA DNS bootstrap registry;
- perform fresh DNS/global-address validation immediately before network I/O;
- bound HTTPS redirects and revalidate every target;
- bound response size;
- distinguish success, not-found, malformed response, remote rate limit and transient unavailability through the typed source-run contract;
- connect catalog, binding, provider registry, shared `ProviderRuntime`, quick research and canonical observation atomically.

No WHOIS fallback, nonpublic RDRS workflow, bulk/reverse lookup or contact harvesting is approved.
