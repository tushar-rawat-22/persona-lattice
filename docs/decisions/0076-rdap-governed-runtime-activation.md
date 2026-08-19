# ADR 0076 — Activate metadata-only RDAP through the governed runtime

Status: accepted

## Context

PersonaLattice already had the hard parts of RDAP in place before activation: one canonical DOMAIN representation, IANA bootstrap selection and caching, SSRF-safe authoritative transport, final-response provenance validation, metadata-only admission, and a typed `routing_unavailable` outcome for bootstrap/routing failure before any authoritative RDAP service is contacted.

Keeping RDAP marked `PLANNED` after those boundaries were proven meant explicit DOMAIN seeds could be normalized and carried through convergence/M5 but could not obtain reviewed registration metadata.

## Decision

Activate `rdap_domain_registry` for explicit DOMAIN research through the existing governed source path.

The source is now:

- `ACTIVE`, source-policy reviewed, zero-direct-cost and credentialless;
- bound only to `LeadKind.DOMAIN`;
- registered as a DEVELOPMENT provider and owned by the process-wide `ProviderRuntime`;
- executed only from an explicit DOMAIN research seed;
- metadata-only: it emits no typed subject leads;
- limited to bounded domain status/nameserver context plus non-identity/redaction flags;
- backed by the existing process-wide IANA DNS RDAP bootstrap cache and SSRF-safe authoritative transport.

Discovered domain clues remain `DISPLAY_ONLY`. Activating RDAP does not turn a domain found in an email, profile or provider response into an automatic recursive request.

## Attempt accounting

Routing authority and subject-provider execution remain distinct phases.

If the IANA bootstrap cache cannot supply a usable current routing snapshot, the source reports `routing_unavailable` with `execution_attempted=false`. That failure is not counted against an authoritative RDAP service.

Once an authoritative RDAP service has been contacted, remote rate limits, transient service failures and malformed returned results use the existing attempted-failure semantics. A valid 404/not-found response is a completed zero-observation result, not a provider failure.

The local ProviderRuntime budget still guards the whole application execution path. It is an application safety limit, not an upstream reliability metric.

## Provenance and privacy

The IANA-bootstrap-derived canonical query URL proves how authority was selected. The final validated HTTPS response URL is retained as the evidence source locator when redirects occur.

Registrant/contact names, organizations, postal addresses, email addresses and telephone numbers are not admitted. Upstream redaction and absent fields remain authoritative. PersonaLattice does not fall back to WHOIS, RDRS/nonpublic disclosure, reverse lookup, bulk enumeration or contact harvesting.

## Consequences

Positive:

- explicit DOMAIN seeds now have useful zero-spend registration context;
- RDAP uses the same catalog/binding/registry/runtime/source-state/provenance contracts as other executable network sources;
- bootstrap/routing outages remain distinguishable from authoritative provider failures;
- activation adds no credential, paid dependency or new automatic recursion.

Costs and limitations:

- RDAP service behavior and rate limits vary across authoritative registries, so the local budget is intentionally conservative and not a claim about a universal upstream quota;
- existing persistent SQLite databases created before DOMAIN was added to M1 may require a deliberate schema recreation/migration before persisting DOMAIN identifiers;
- registration metadata is context, not evidence that a registrant/contact identity belongs to the investigated subject.

## Unchanged boundaries

Production recursion remains depth 2 / 12 nodes. M5 remains uncalibrated evidence-strength triage, `is_identity_claim=false` remains fixed, and `hard_contradiction` remains a production veto.
