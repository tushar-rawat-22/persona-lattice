# ADR 0020 — Public DNS infrastructure uses the governed runtime

Status: accepted for V2-D migration

## Context

After GitHub, GitLab and Codeforces moved onto the shared `ProviderRuntime`, public DNS remained a direct network call in `research.py`. The existing resolver was already deliberately narrow: it resolved only the hostname of a normalized public URL, retained globally routable addresses only, capped the result set, and explicitly stated that those addresses describe public website/domain infrastructure rather than a person's device or location.

Leaving that network call outside the provider boundary nevertheless meant its execution did not share the runtime's purpose policy, process-wide concurrency/rate state, timeout boundary and response-contract validation.

## Decision

Introduce `PublicDnsInfrastructureProvider` and register `public_dns_infrastructure` as a reviewed development provider owned by the process-wide `ProviderRuntime`.

The provider:

- accepts only normalized HTTP(S) URL identifiers in the currently executable path;
- extracts the URL hostname itself and rejects credential-bearing URLs;
- sends no credential, token or API key;
- uses the existing bounded system resolver rather than adding a third-party DNS service;
- preserves the existing globally-routable-address filter and eight-address ceiling in `network_metadata.py`;
- independently revalidates resolver output as IP addresses, rejects any non-global result, enforces the eight-address ceiling again, canonicalizes addresses and de-duplicates them before admission;
- treats an empty/NXDOMAIN-style result as valid no-observation output;
- maps resolver `OSError` failures to a transient provider failure;
- emits a `dns://<hostname>` source locator;
- labels returned addresses only as `public_infrastructure_ips`;
- fixes `personal_device_ip_claim=false` and `physical_location_claim=false` in the provider payload.

Production URL quick research now sends the normalized URL through the shared runtime. The existing injected `network_lookup(hostname)` seam remains test compatibility only and does not own production execution.

## Domain seeds remain closed

The V2 source capability can conceptually accept `DOMAIN`, but current quick research has no domain research kind/runtime route. This migration intentionally binds only `URL`. It does not silently create a domain-seed execution surface.

## Runtime policy

The descriptor uses one attempt, a four-second timeout, a 16 KiB serialized-result ceiling, concurrency two, and a local 30-per-60-second budget. This is a PersonaLattice application budget, not a claim about a universal DNS upstream quota; system resolvers vary by environment. The purpose of the budget is to bound recursive application behavior before resolver/network I/O.

## Privacy boundary

A public hostname can resolve to CDN, hosting, load-balancer or other shared infrastructure. Those addresses must never be promoted into evidence that a subject owns, uses, or is physically located at an IP address. No reverse-IP enumeration, geolocation, passive-DNS history, WHOIS enrichment, device discovery or live tracking is added by this migration.

## Consequences

Positive:

- all current zero-direct-cost network sources except optional Brave now use the shared governed runtime;
- DNS execution shares process-wide policy, rate, concurrency and timeout controls;
- source binding metadata can no longer classify DNS as legacy research;
- provider output makes the infrastructure-only semantics explicit at the adapter boundary;
- a future resolver implementation cannot bypass the provider's global-IP and result-count checks.

Costs:

- DNS now consumes a provider-runtime budget even though the underlying resolver is local/system-provided;
- domain-seed support remains intentionally incomplete until a separate research-kind/runtime decision is made.

## Next migration

Optional Brave exact-identifier search is the only remaining legacy network binding. It should be migrated separately because it is metered and credentialed; zero-spend recursion must continue to operate without it, and a runtime migration must not accidentally make the optional paid/metered path mandatory.
