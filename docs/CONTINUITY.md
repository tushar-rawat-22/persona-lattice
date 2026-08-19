# Continuity

Public-safe engineering handover for PersonaLattice. Verify GitHub before changing anything; this file is a checkpoint, not authority over the repository.

Never place API keys, real research identifiers, retained-case data, password hashes, session material, raw consent evidence or unredacted investigation screenshots here.

## Repository checkpoint

- Repository: `tushar-rawat-22/persona-lattice`
- Default branch: `main`
- Local checkout convention: `~/persona-lattice`
- License: Apache-2.0 for original code
- Operating model: one authenticated operator; public route is demo/preview only
- PR #136: canonical DOMAIN reachability for the RDAP activation sequence
- Exact tested implementation head before documentation: `ca9818ba101cb0565ed7e40642aee2232d6f443a`
- Exact-head CI: run `32288646149`; API 3.11 PASS, API 3.13 PASS, web PASS, deployment-image PASS
- Open activation blocker: Issue #133 — DOMAIN representation is closed by PR #136; atomic RDAP provider activation remains
- Relevant RDAP ADRs: `0069-rdap-domain-admission-preflight.md`, `0070-rdap-metadata-only-source-contract.md`, `0071-rdap-authoritative-transport.md`, `0072-rdap-bootstrap-cache.md`, `0073-rdap-final-response-provenance.md`, `0074-rdap-routing-unavailable-non-attempt.md`, `0075-domain-identifier-reachability.md`
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
- RDAP: admission, metadata-only contract, authoritative SSRF-safe transport, process-wide IANA bootstrap cache, final-response provenance and routing non-attempt accounting are complete through PR #134. PR #136 adds canonical DOMAIN reachability. RDAP itself remains PLANNED, unbound, source-policy-unreviewed and non-recursive until its activation PR is green.
- M10: deterministic replay, source/graph accounting, real-engine factor ablations, label-provenance manifests and consented-only accounting exist. Representative consented evaluation/calibration remains incomplete.

## Latest block — canonical DOMAIN reachability

Issue #133 originally looked like a small `ResearchKind.DOMAIN` addition. That was wrong: live M5 maps every converged node through M1 `IdentifierKind`, and the V2 lead graph had its own weaker domain canonicalizer. Adding only a research enum would have created a half-supported seed type and another normalization authority.

PR #136 fixes the representation end to end without activating RDAP:

- `IdentifierKind.DOMAIN` is now part of M1;
- M1 normalizes explicit public DNS names conservatively, including IDNA A-label canonicalization;
- URLs, IP literals, local-use names, malformed labels and whitespace-bearing values fail closed;
- `LeadKind.DOMAIN` delegates to M1 instead of using a graph-only normalizer;
- RDAP admission delegates to the same M1 domain normalizer;
- `ResearchKind.DOMAIN` is executable;
- explicit domain seeds pass through quick research, convergence and ephemeral live M5;
- until RDAP is activated, explicit domain quick research returns a truthful normalized zero-observation/zero-attempt report;
- discovered domain clues remain `DISPLAY_ONLY` and cannot become automatic recursive pivots.

The exact implementation head `ca9818ba101cb0565ed7e40642aee2232d6f443a` passed the complete CI matrix in run `32288646149` before the roadmap/continuity edits were added.

One operational caveat remains explicit: existing persistent M1 databases created with the older SQLite enum constraint are not silently rewritten. Any deployment that persists that evidence schema must recreate or deliberately migrate the constraint before storing DOMAIN identifiers. The live converged M5 graph uses its own ephemeral schema and is covered by the new end-to-end test.

ADR 0075 records this decision.

## RDAP activation boundary

RDAP is still non-executable. No provider registry descriptor, source binding, shared `ProviderRuntime` adapter or subject-provider request is enabled by PR #136.

The privacy contract remains metadata-only: `rdap_domain_registry.emits = frozenset()`. Registrant/contact names, organizations, addresses, email addresses and telephone numbers remain excluded. Upstream redaction and missing fields remain authoritative. No WHOIS fallback, RDRS/nonpublic lookup, reverse/bulk search or contact harvesting is approved.

`routing_unavailable` remains the typed non-attempt state for an unusable IANA/bootstrap routing prerequisite. Failures after an authoritative RDAP service has actually been contacted must use the existing attempted-failure semantics instead.

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

Keep Issue #133 open through the RDAP activation PR.

1. implement the metadata-only RDAP provider using the existing admission, bootstrap cache and SSRF-safe authoritative transport;
2. wire it atomically through source catalog review → binding → DEVELOPMENT provider registry → process-wide `ProviderRuntime` → DOMAIN quick research → typed source-run reporting → canonical observation;
3. prove deterministic success, not-found, malformed, remote-rate-limit, provider-unavailable and bootstrap/routing-unavailable outcomes;
4. prove bootstrap/routing failure consumes zero RDAP provider attempts while failures after authoritative provider contact do consume an attempt;
5. preserve canonical bootstrap-query versus final-response provenance and authoritative redaction;
6. keep discovered domain clues display-only and production recursion at depth 2 / 12 nodes.

For M10, the highest-value unresolved need remains genuinely consented or independently reviewed label evidence. Do not relabel synthetic regression fixtures as consented to manufacture progress.

WebFinger remains planned unless a concrete host passes the exact-host source-policy gate. Gravatar remains blocked on its privacy-policy requirement. ActivityPub actor fetching remains separate and unapproved.

## Update discipline

For every meaningful block record verified main/branch/PR state, CI evidence, behavior changes, explicit non-changes, corrected assumptions, unresolved risks and the exact next gate. Keep public/operator prose separate from assistant handover prose.
