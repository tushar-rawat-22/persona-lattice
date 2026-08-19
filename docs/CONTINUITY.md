# Continuity

Public-safe engineering handover for PersonaLattice. Verify GitHub before changing anything; this file is a checkpoint, not authority over the repository.

Never place API keys, real research identifiers, retained-case data, password hashes, session material, raw consent evidence or unredacted investigation screenshots here.

## Repository checkpoint

- Repository: `tushar-rawat-22/persona-lattice`
- Default branch: `main`
- Local checkout convention: `~/persona-lattice`
- License: Apache-2.0 for original code
- Operating model: one authenticated operator; public route is demo/preview only
- Main before PR #132: `42cb8f1759b1ed41bb9505b887eb4264eafaedd7`
- PR #132: RDAP final-response provenance correction before activation
- Exact tested implementation head before continuity update: `c6ba4716e29df4fd874d0eddb59b3d9c7f8a7443`
- Exact-head CI: run `32276834735`; API 3.11 PASS, API 3.13 PASS, web PASS, deployment-image PASS
- Open activation blocker: Issue #133 — DOMAIN reachability plus bootstrap/non-attempt accounting
- Relevant RDAP ADRs: `0069-rdap-domain-admission-preflight.md`, `0070-rdap-metadata-only-source-contract.md`, `0071-rdap-authoritative-transport.md`, `0072-rdap-bootstrap-cache.md`, `0073-rdap-final-response-provenance.md`
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
- RDAP: admission, metadata-only contract, authoritative SSRF-safe transport, process-wide IANA bootstrap cache and final-response provenance contract are complete through PR #132. RDAP itself remains PLANNED, unbound, source-policy-unreviewed and non-recursive.
- M10: deterministic replay, source/graph accounting, real-engine factor ablations, label-provenance manifests and consented-only accounting exist. Representative consented evaluation/calibration remains incomplete.

## Latest block — RDAP final-response provenance

PR #132 fixes a provenance bug without activating RDAP subject research.

The transport already preserved both the IANA-bootstrap-derived canonical domain query and the final HTTPS URL that returned an RDAP object after any admitted redirects. The admission layer previously forced retained `source_locator` to equal the initial query URL. That would have retained where the request started instead of where redirected evidence was actually returned.

ADR 0073 now separates the two roles:

- `canonical_query_url` proves that routing began from the exact RFC 9082 domain query selected through IANA bootstrap data;
- `source_locator` is the final canonical HTTPS URL that actually returned the admitted object and owns retained evidence provenance.

The final locator is independently constrained to HTTPS, a DNS hostname, default HTTPS port, no credentials and no fragment. Fresh DNS/global-address validation remains the transport's responsibility on every hop.

Regression coverage proves redirected final provenance is retained and rejects HTTP downgrade, credential-bearing URLs, IP literals, non-default ports and fragments. Existing non-redirected admission remains compatible.

### Primary-source basis rechecked 2026-08-19

- RFC 9082 defines domain queries by appending `domain/<domain>` to an authoritative RDAP base URL.
- RFC 9224 requires label-wise longest-match bootstrap selection and permits equivalent authoritative services; clients should cache bootstrap registries rather than fetch them on every request.
- IANA remains the authoritative DNS RDAP bootstrap registry publisher and exposes `dns.json`.
- IANA's current RDAP server requirements explicitly account for 3xx redirects, 4xx not-found behavior, 200 domain objects and 429 rate-limit responses.
- IANA protocol-registry data remains intended for free use; this does not override downstream registration-data privacy rights.
- ICANN's Registration Data Policy was revised on 12 May 2026; PersonaLattice continues to treat nonpublic registration data as outside this public metadata source.

## RDAP activation blockers found during adversarial review

The previous handover said the next step could be one immediate atomic activation. That was too optimistic. Two additional execution-contract gaps must be closed first, and Issue #133 records them.

### 1. DOMAIN is not executable quick research

The V2 graph has `LeadKind.DOMAIN`, and RDAP accepts DOMAIN at the capability layer, but `ResearchKind` currently exposes only username, phone, email and URL. `run_quick_research()` therefore cannot execute a domain seed, and convergence cannot construct a DOMAIN research node.

Activation must not make the catalog claim executable domain coverage until a bounded DOMAIN route exists. The current extractor policy also keeps discovered domain fields display-only; do not silently change that recursion policy as part of provider activation.

### 2. IANA bootstrap failure is routing failure, not RDAP provider failure

The process-wide IANA bootstrap cache is routing authority. If it cannot supply a current usable registry snapshot, no authoritative RDAP subject provider has been contacted.

Typed source-state reporting therefore needs an explicit non-attempt routing/bootstrap-unavailable outcome before RDAP enters the shared provider runtime. Do not classify that state as `execution_failure`, `remote_rate_limit`, or malformed RDAP provider output merely because the adapter would otherwise sit inside ProviderRuntime.

Deterministic tests must prove bootstrap failure contributes zero RDAP provider attempts while failures after authoritative RDAP contact count as attempts according to the existing phase-proven source contract.

## RDAP remains non-executable

PR #132 intentionally does **not** add a provider registry descriptor, source binding, shared `ProviderRuntime` adapter, domain-seed quick-research route or provider network execution.

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

Close Issue #133 before RDAP activation:

1. add a bounded explicit DOMAIN quick-research route without broadening display-only domain recursion;
2. add a truthful bootstrap/routing-unavailable non-attempt source outcome and deterministic accounting tests;
3. only then perform one atomic governed RDAP activation through source catalog → binding → provider registry → process-wide `ProviderRuntime` → typed source-run reporting → canonical metadata-only observation.

The activation must preserve exact canonical-query/final-response provenance, authoritative redaction, metadata-only output and zero-spend operation.

For M10, the highest-value unresolved need remains genuinely consented or independently reviewed label evidence. Do not relabel synthetic regression fixtures as consented to manufacture progress.

WebFinger remains planned unless a concrete host passes the exact-host source-policy gate. Gravatar remains blocked on its privacy-policy requirement. ActivityPub actor fetching remains separate and unapproved.

## Update discipline

For every meaningful block record verified main/branch/PR state, CI evidence, behavior changes, explicit non-changes, corrected assumptions, unresolved risks and the exact next gate. Keep public/operator prose separate from assistant handover prose.
