# Continuity

Public-safe engineering handover for PersonaLattice. Verify GitHub before changing anything; this file is a checkpoint, not authority over the repository.

Never place API keys, real research identifiers, retained-case data, password hashes, session material, raw consent evidence or unredacted investigation screenshots here.

## Repository checkpoint

- Repository: `tushar-rawat-22/persona-lattice`
- Default branch: `main`
- Local checkout convention: `~/persona-lattice`
- License: Apache-2.0 for original code
- Operating model: one authenticated operator; public route is demo/preview only
- PR #134: RDAP routing/bootstrap non-attempt accounting — merged
- Exact tested implementation head: `5965902a528d820a7b7ff85b4475066fcc4080b7`
- Exact-head CI: run `32282843181`; API 3.11 PASS, API 3.13 PASS, web PASS, deployment-image PASS
- PR #134 merge commit / main checkpoint: `94120f9549a0380640eee78daefceb60dcd20684`
- Open activation blocker: Issue #133 — DOMAIN reachability remains; routing/bootstrap non-attempt accounting is closed
- Relevant RDAP ADRs: `0069-rdap-domain-admission-preflight.md`, `0070-rdap-metadata-only-source-contract.md`, `0071-rdap-authoritative-transport.md`, `0072-rdap-bootstrap-cache.md`, `0073-rdap-final-response-provenance.md`, `0074-rdap-routing-unavailable-non-attempt.md`
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
- RDAP: admission, metadata-only contract, authoritative SSRF-safe transport, process-wide IANA bootstrap cache, final-response provenance and routing non-attempt accounting are complete through PR #134. RDAP itself remains PLANNED, unbound, source-policy-unreviewed and non-recursive.
- M10: deterministic replay, source/graph accounting, real-engine factor ablations, label-provenance manifests and consented-only accounting exist. Representative consented evaluation/calibration remains incomplete.

## Latest block — RDAP routing failure accounting

Issue #133 identified two pre-activation gaps. PR #134 closes the accounting half without activating RDAP.

A typed `routing_unavailable` reason now sits under `SourceRunState.UNAVAILABLE`. It is explicitly a **non-attempt** state: zero observations, terminal for the current source action, and excluded from provider attempt/failure counts. `source_routing_unavailable_record()` is the construction authority, and deterministic source-evaluation counters expose `routing_unavailable_count` separately.

This outcome is intended for prerequisite authority/routing failures such as the process-wide IANA bootstrap cache being unable to supply a current usable DNS RDAP registry snapshot. It is deliberately not mapped by the generic provider-exception mapper, because no authoritative subject provider has been contacted at that point.

The first CI pass exposed one stale exact-shape source-run projection test after the new counter was added. The counter was kept; the exact contract expectation was corrected. The final head then passed the full matrix in run `32282843181`.

ADR 0074 records the decision. The state/reason fixture matrix, direct outcome tests and retained-report projection tests now prove that routing unavailability contributes zero source attempts and zero attempted provider failures.

## Corrected DOMAIN-reachability assessment

The earlier handover described the remaining DOMAIN work as a small `ResearchKind.DOMAIN` addition. That was too shallow.

Three layers currently disagree:

1. the V2 graph has `LeadKind.DOMAIN` and RDAP admission already validates bare domains;
2. `ResearchKind` exposes only username, phone, email and URL;
3. M1 `IdentifierKind` also has no DOMAIN, and `evaluate_live_m5()` maps every converged research node through `IdentifierKind(node.kind.value)` plus canonical M1 normalization.

Therefore adding `ResearchKind.DOMAIN` alone would create a half-supported seed type: quick research might be made to parse it, but converged retention/M5 would fail or require an ad-hoc normalization bypass. Do **not** patch around M1/M5 merely to activate RDAP quickly.

The next DOMAIN block must decide and test the canonical representation end to end. It may add a bounded DOMAIN identifier kind to M1 if that is the cleanest consistent design, but that change must preserve existing identifier semantics and must not turn discovered domain clues into automatic recursion. The existing domain lead disposition stays display-only unless a separate evaluated policy change explicitly authorizes otherwise.

## RDAP remains non-executable

No provider registry descriptor, source binding, shared `ProviderRuntime` adapter or RDAP subject-provider call is active yet.

The RDAP privacy contract remains metadata-only: `rdap_domain_registry.emits = frozenset()`. Registrant/contact names, organizations, addresses, email addresses and telephone numbers remain excluded. Upstream redaction and missing fields remain authoritative.

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

Keep Issue #133 open until DOMAIN reachability is genuinely end-to-end:

1. define one canonical DOMAIN identifier/normalization path that is consistent across quick research, convergence and the ephemeral M1/M5 graph;
2. prove an explicit DOMAIN seed can run without changing the display-only disposition of discovered domain clues;
3. preserve the now-merged routing/bootstrap non-attempt semantics while proving failures after authoritative RDAP contact use the existing attempted-failure semantics;
4. only then perform one atomic governed RDAP activation through source catalog → binding → provider registry → process-wide `ProviderRuntime` → typed source-run reporting → canonical metadata-only observation.

The activation must preserve exact canonical-query/final-response provenance, authoritative redaction, metadata-only output and zero-spend operation.

For M10, the highest-value unresolved need remains genuinely consented or independently reviewed label evidence. Do not relabel synthetic regression fixtures as consented to manufacture progress.

WebFinger remains planned unless a concrete host passes the exact-host source-policy gate. Gravatar remains blocked on its privacy-policy requirement. ActivityPub actor fetching remains separate and unapproved.

## Update discipline

For every meaningful block record verified main/branch/PR state, CI evidence, behavior changes, explicit non-changes, corrected assumptions, unresolved risks and the exact next gate. Keep public/operator prose separate from assistant handover prose.
