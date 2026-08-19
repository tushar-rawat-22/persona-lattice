# ADR 0071 — RDAP authoritative transport stays separate from activation

Status: accepted for source-expansion pre-activation

## Context

RDAP admission already accepts explicit public DNS domains, selects service URLs from IANA-style bootstrap data and retains only bounded registration metadata. The source is still planned and non-executable.

A transport is needed before activation, but a generic HTTP client would weaken two existing boundaries. RDAP endpoints come from remote bootstrap data and can redirect, so every network hop needs fresh SSRF admission. RDAP bootstrap selection also follows RFC 9224 longest-label matching rather than assuming the final TLD is always the most specific authority.

## Decision

Add a dedicated RDAP transport without registering or binding the source yet.

The transport:

- receives a caller-supplied IANA-style bootstrap document rather than downloading it for every research request;
- selects only the longest matching DNS bootstrap suffix and combines equivalent longest entries in registry order;
- constructs the RFC 9082 `domain/<name>` query from admitted HTTPS base URLs;
- resolves each request and redirect hostname immediately before I/O;
- rejects malformed, non-global or excessive DNS answers;
- pins TCP to an admitted address while validating TLS against the DNS hostname;
- sends `Accept: application/rdap+json` and accepts only that RDAP media type on a successful response;
- bounds each response to 64 KiB, each connection to four seconds and redirects to three;
- treats 404 as a completed no-result response;
- preserves 429 as a remote rate-limit outcome rather than falling through to another equivalent service;
- treats 408 and selected 5xx responses or connection failures as transient;
- may try the next equivalent bootstrap URL only after transient unavailability;
- revalidates every redirect, including fresh DNS admission;
- classifies an unsafe redirect discovered after provider contact as returned-result validation failure, not a pre-call policy rejection.

The result retains both the canonical bootstrap-derived query URL and the final response URL so later provider activation can choose exact provenance without pretending a redirected response came from the original URL.

## Boundaries

This does not activate `rdap_domain_registry`. The source remains `PLANNED`, unbound, source-policy-unreviewed and non-recursive. No provider registry entry, shared-runtime owner or quick-research path is added here.

The transport does not fetch nonpublic registration data, use WHOIS fallback, call RDRS, perform reverse/bulk search or recover fields redacted by the authoritative service. The metadata-only admission contract from ADR 0070 remains unchanged.

The bootstrap document itself will need a bounded refresh/cache authority before activation. Fetching IANA bootstrap data on every research request is not approved.

## Consequences

Positive:

- authoritative endpoint selection now follows RFC 9224 longest-match behavior;
- redirect and DNS-rebinding risks are covered before source activation;
- not-found, rate-limit, transient and malformed outcomes have deterministic transport semantics;
- the future provider can remain a thin governed adapter over an already-tested network boundary.

Cost:

- RDAP still requires another atomic activation block covering bootstrap refresh/cache ownership, provider registration, binding, shared runtime, typed source-state mapping and canonical observation admission.

Production recursion remains depth 2 / 12 nodes, required spend remains zero, and M5 remains uncalibrated evidence-strength triage rather than identity probability.
