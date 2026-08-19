# ADR 0072 — Cache IANA RDAP bootstrap authority before activation

Status: accepted for RDAP pre-activation

## Context

RDAP domain routing depends on IANA's DNS bootstrap registry at `https://data.iana.org/rdap/dns.json`. RFC 9224 says clients should not fetch the bootstrap registry for every RDAP request and should cache it using HTTP freshness information.

The existing RDAP transport intentionally accepts caller-supplied bootstrap data. That avoided per-request IANA traffic, but it left ownership of refresh, freshness and concurrent access undefined.

## Decision

Add one process-local `IanaRdapBootstrapCache` for the fixed IANA DNS bootstrap URL.

The cache:

- fetches only `https://data.iana.org/rdap/dns.json`;
- uses ordinary certificate-validated HTTPS to that fixed, non-user-controlled authority and does not follow redirects;
- bounds the response at 128 KiB and requires the RFC 9224 `application/json` media type plus a bounded `services` structure;
- reuses a fresh snapshot without network I/O;
- follows `Cache-Control: max-age` when present, otherwise `Expires`, using the response `Date` when available to avoid local clock skew, with a 24-hour fallback and a seven-day maximum local TTL;
- treats `no-cache` as immediately stale and does not retain `no-store` responses;
- preserves ETag and Last-Modified validators for conditional refresh;
- accepts HTTP 304 only when a prior snapshot exists;
- serializes refresh under one async lock so concurrent first/expired reads cannot create a refresh stampede;
- returns copies so callers cannot mutate the cached authority document;
- does not serve an expired snapshot if refresh fails.

The last rule deliberately favors routing correctness over availability. An arbitrarily stale bootstrap can direct a domain to an authority that IANA no longer identifies as current.

## Why the bootstrap fetch is separate from provider execution

The IANA registry is routing metadata used to discover the authoritative RDAP service; it is not subject evidence and is not itself a PersonaLattice research provider. Its refresh errors therefore use dedicated bootstrap exceptions rather than being counted automatically as a contacted subject-data provider failure.

A later RDAP activation must map bootstrap-unavailable state deliberately at the provider boundary.

## Zero-spend and privacy effect

The IANA bootstrap registry is public protocol-registry data and requires no PersonaLattice credential or paid service. The cache stores only public authority metadata in process memory. It does not persist subject identifiers, RDAP responses or case data.

## Non-changes

This ADR does not activate `rdap_domain_registry`, add a source binding/provider descriptor/runtime owner, create domain-seed execution, add WHOIS fallback, use RDRS/nonpublic data, expand recursion, or change M5 semantics.

## Next gate

Integrate the cache into one governed RDAP provider and activate the source atomically through source catalog, binding, provider registry, shared `ProviderRuntime`, typed source-run reporting and canonical observation admission. Provider activation must retain the existing metadata-only field contract and deterministic success/not-found/malformed/rate-limit/unavailable fixtures.
