# Continuity

Public-safe engineering handover for PersonaLattice. Verify GitHub before changing anything; this file is a checkpoint, not authority over the repository.

Never place API keys, real research identifiers, retained-case data, password hashes, session material, raw consent evidence or unredacted investigation screenshots here.

## Repository checkpoint

- Repository: `tushar-rawat-22/persona-lattice`
- Default branch: `main`
- Local checkout convention: `~/persona-lattice`
- License: Apache-2.0 for original code
- Operating model: one authenticated operator; public route is demo/preview only
- Main before PR #130: `a04b9063eec28903431e7f66af40aeaf71024cc4`
- PR #130: bounded process-wide IANA RDAP bootstrap cache
- Exact tested PR #130 head: `2d4c73b5346420a2c2571fdf2c5ac8d8e8fef35e`
- Exact-head CI: run `32271318756`; API 3.11 PASS, API 3.13 PASS, web PASS, deployment-image PASS
- PR #130 merge: `0247737aa64b159e96c6075c2c94f2ad5513d013`
- Relevant RDAP ADRs: `0069-rdap-domain-admission-preflight.md`, `0070-rdap-metadata-only-source-contract.md`, `0071-rdap-authoritative-transport.md`, `0072-rdap-bootstrap-cache.md`
- Documentation standard: `docs/DOCUMENTATION_STANDARD.md`
- Zero-spend runbook: `docs/ZERO_SPEND_RUNBOOK.md`
- Optional paid Render reference: `deploy/render-paid.yaml`

## Milestone state

- M0-M6: complete.
- M7 private one-admin product: implemented and manually accepted locally.
- M8 privacy lifecycle/operations: substantially implemented.
- M9 private convergence: implemented.
- V2-A typed lead graph: complete, PR #20.
- V2-B deterministic frontier: complete, PR #21.
- V2-C source capability registry/planner: complete, PR #22.
- V2-D runtime consistency and architecture closure: complete, PRs #89-#90.
- Bluesky public profiles: active for valid AT handles through the governed runtime, PR #98.
- Gravatar: admission preflight complete; still PLANNED because its provider-terms/privacy-policy gate is unresolved.
- WebFinger: parser/admission, SSRF transport, URL-only semantics and exact-host policy are complete; still PLANNED because no concrete host has passed the exact-host source-policy gate.
- RDAP: admission, metadata-only contract, authoritative SSRF-safe transport and process-wide IANA bootstrap cache are complete through PR #130. RDAP itself remains PLANNED, unbound, source-policy-unreviewed and non-recursive.
- M10: deterministic replay, source/graph accounting, real-engine factor ablations, label-provenance manifests and consented-only accounting exist. Representative consented evaluation/calibration remains incomplete.

## Latest block — IANA RDAP bootstrap cache

PR #130 closes the routing-authority ownership gap without activating RDAP subject research.

### Primary-source basis

RFC 9224 says RDAP clients should not fetch IANA bootstrap registries on every RDAP request and should cache them using HTTP freshness signaling. It also requires the JSON bootstrap registry to be served as `application/json`.

The fixed domain bootstrap authority is `https://data.iana.org/rdap/dns.json`. This registry is routing metadata, not subject evidence.

### Cache contract

`rdap_bootstrap_cache.py` now provides one process-wide `IANA_RDAP_BOOTSTRAP_CACHE` that:

- fetches only the fixed IANA DNS bootstrap URL;
- uses normal certificate-validated HTTPS and does not follow redirects;
- bounds responses at 128 KiB and validates a bounded `services` structure;
- requires `application/json` for a successful bootstrap response;
- reuses fresh state without another IANA request;
- honors `Cache-Control: max-age`, otherwise `Expires`, using response `Date` when available;
- uses a 24-hour fallback freshness lifetime capped at seven days;
- treats `no-cache` as immediately stale and does not retain `no-store` responses;
- retains ETag/Last-Modified validators for conditional refresh;
- accepts 304 only when a prior snapshot exists;
- serializes refresh under one async lock to avoid request stampedes;
- returns deep copies so research code cannot mutate cached authority data;
- does not silently serve an expired snapshot when refresh fails.

Bootstrap refresh errors use dedicated bootstrap exceptions. They are not automatically classified as contacted subject-provider failures because IANA bootstrap retrieval is routing metadata, not a research provider call.

### Flaws corrected during review

Three issues were fixed before the exact green head was merged:

1. The first version also accepted `application/rdap+json`. RFC 9224 requires `application/json` for the bootstrap registry, so the media-type gate is now strict.
2. The first version treated `no-store` only as zero freshness but still retained the snapshot object. It now does not cache `no-store` responses at all; `Expires` freshness also uses origin `Date` when available.
3. The first version provided a cache class but no process-wide owner. A module singleton now makes ownership explicit so the later RDAP provider cannot accidentally recreate per-request caches.

Regression tests cover fresh reuse, conditional 304 refresh, origin-date `Expires`, no-store behavior, expired-refresh failure, malformed/media-type/redirect rejection, concurrent refresh serialization, returned-payload isolation and the process-wide owner.

## RDAP remains non-executable

PR #130 intentionally does **not** add a provider registry descriptor, source binding, shared `ProviderRuntime` adapter, domain-seed quick-research route or provider network execution.

The existing RDAP privacy contract remains metadata-only: `rdap_domain_registry.emits = frozenset()`. Registrant/contact names, organizations, addresses, email addresses and telephone numbers remain excluded. Upstream redaction and missing fields remain authoritative.

No WHOIS fallback, RDRS/nonpublic lookup, reverse/bulk search or contact harvesting is approved.

## Current controlled evaluation checkpoint

Production depth 2 / 12 nodes: 9 labelled admitted pivots (8 relevant, 1 wrong), 11 simulated attempts and 11 request-cost units.

Candidate depth 3 / 12 nodes: 12 labelled admitted pivots (8 relevant, 4 wrong), 14 attempts and 14 request-cost units.

Controlled delta depth 2 → 3: +3 attempts, +3 wrong-labelled pivots and +0 relevant pivots. This is synthetic regression evidence only; production remains depth 2 / 12 nodes.

Controlled M5 omission results under `m5-evidence-strength-v1` remain diagnostic only. `hard_contradiction` remains a production veto, M5 remains uncalibrated evidence-strength triage and `is_identity_claim=false` remains fixed.

## Permanent boundaries

- Required operation remains zero paid APIs, zero paid database, zero paid hosting requirement, zero paid proxy network and zero paid enrichment.
- Planned/review/manual/reference sources remain non-executable.
- Uploaded content is untrusted data; extraction is never execution authority.
- No private-account bypass, account-recovery enumeration, password/OTP/session/token collection, CAPTCHA/WAF/proxy/Tor evasion, hidden KYC/government-ID acquisition, covert personal/device IP discovery, live tracking, covert subject contact or regulated eligibility decisioning.

## Next gate

For source expansion, complete one **atomic governed RDAP activation** through source catalog → binding → provider registry → process-wide `ProviderRuntime` → typed source-run reporting → canonical observation.

Activation must preserve metadata-only output, authoritative redaction, exact query/final-response provenance, zero-spend operation and deterministic success/not-found/malformed/rate-limit/unavailable fixtures. Bootstrap-unavailable state must be mapped truthfully without pretending an RDAP subject provider was contacted when only IANA routing metadata failed.

For M10, the highest-value unresolved need remains genuinely consented or independently reviewed label evidence. Do not relabel synthetic regression fixtures as consented to manufacture progress.

WebFinger remains planned unless a concrete host passes the exact-host source-policy gate. Gravatar remains blocked on its privacy-policy requirement. ActivityPub actor fetching remains separate and unapproved.

## Update discipline

For every meaningful block record verified main/branch/PR state, CI evidence, behavior changes, explicit non-changes, corrected assumptions, unresolved risks and the exact next gate. Keep public/operator prose separate from assistant handover prose.
