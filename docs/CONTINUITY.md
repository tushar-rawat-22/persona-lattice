# Continuity

Public-safe engineering handover for PersonaLattice. Verify GitHub before changing anything; this file is a checkpoint, not authority over the repository.

Never place API keys, real research identifiers, retained-case data, password hashes, session material, raw consent/review evidence or unredacted investigation screenshots here.

## Repository checkpoint

- Repository: `tushar-rawat-22/persona-lattice`
- Default branch: `main`
- Local checkout convention: `~/persona-lattice`
- License: Apache-2.0 for original code
- Operating model: one authenticated operator; public route is demo/preview only
- Verified main before this block: `a9b8c1db79548fc30e9d75ec24999d4ad2f1f090`
- PR #137: governed metadata-only RDAP activation — merged
- PR #138: bounded local consented M10 cohort runner — merged
- PR #139: independently reviewed M10 provenance boundary — merged
- PR #140: shared private local M10 materializer + reviewed runner — merged
- PR #142: operator DOMAIN research reachability — merged
- PR #142 exact tested head: `f3729a48705ba8ab349fb6cef1217cd9c5f5d921`
- PR #142 exact-head CI: run `32304516425`; API 3.11 PASS, API 3.13 PASS, web PASS, deployment-image PASS
- Issue #141: closed by PR #142
- Current branch: `feat/operator-pivot-evidence-context`
- Current block: expose the exact canonical observation field and observation context that caused each resolvable evidence pivot
- Current exact-head CI: pending; merge only after the complete required matrix passes
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
- Bluesky public profiles: active for valid AT handles, PR #98.
- RDAP: active for explicit DOMAIN seeds through the governed runtime, PR #137; operator UI reachability complete in PR #142.
- Gravatar: PLANNED; blocked on provider privacy-policy/free-key requirements.
- WebFinger: PLANNED; parser/admission, SSRF transport, URL-only semantics and exact-host policy are complete, but no concrete host is approved.
- M10: deterministic replay, source/graph accounting, real-engine factor ablations, three-way label provenance (`synthetic`, `consented`, `independently_reviewed`), strict consented/reviewed-only accounting and shared private local cohort ingestion are implemented. Representative real evaluation remains incomplete.

## Current block — operator pivot evidence context

The retained converged report already carries canonical provenance references for admitted pivots: an edge points to one admitted lead decision, that decision identifies the parent observation index and exact source field, and the parent observation owns the provider source/locator and summary.

Before this block, the private operator UI resolved that chain only far enough to show the provider source and locator. That answered where the evidence came from but not which exact observation field caused the pivot. The operator then had to scan the parent node's raw observation JSON manually.

The current branch extends the existing fail-closed resolver rather than changing the retained schema. For new canonical-reference cases it returns the exact `source_field` and the canonical observation summary together with the existing source and source locator. Pivot cards show that context directly.

Historical self-contained edges retained before ADR 0044 still render through the existing read-only compatibility path. They do not invent a source field or observation summary that was never retained; the UI labels the historical field as unavailable instead.

The resolver still rejects mixed legacy/reference shapes, missing/out-of-range decision references, non-admitted decisions, parent/child/reason mismatches, missing observation references, empty source/locator values and source fields that are not present in the referenced observation details.

This is a presentation/useability change over existing canonical evidence. It adds no retained personal data, provider field, network request, permission, new inference, graph recursion or identity semantic.

## RDAP checkpoint

The live path remains:

`explicit DOMAIN seed → M1 DOMAIN normalization → rdap_domain_registry binding → DEVELOPMENT provider descriptor → process-wide ProviderRuntime → process-wide IANA bootstrap cache → SSRF-safe authoritative RDAP transport → metadata-only observation → typed source-run report → canonical converged evidence`

RDAP remains metadata-only. Registrant/contact names, organizations, addresses, email addresses and telephone numbers are excluded even when an upstream response contains them. No WHOIS fallback, RDRS/nonpublic lookup, reverse/bulk enumeration or contact harvesting is approved.

`routing_unavailable` remains a non-attempt outcome. Once an authoritative RDAP provider has actually been contacted, remote rate limits, transient failures and malformed returned results use attempted-failure semantics. Discovered domains remain `DISPLAY_ONLY`; only explicit DOMAIN seeds execute RDAP.

Existing persistent SQLite databases created before DOMAIN was added to the M1 enum constraint may require deliberate recreation/migration before persisting DOMAIN identifiers.

## M10 checkpoint

The two private evidence-backed entry points share one bounded local materializer. The consented command fixes provenance to `CONSENTED`; the reviewed command fixes it to `INDEPENDENTLY_REVIEWED`. Input JSON cannot promote its own evidence basis.

The runners keep the 1 MiB input, 256-fixture and 2,048-node bounds, M1-backed normalization, production depth-2 / 12-node baseline and depth-3 / 12-node diagnostic candidate. They emit aggregate accounting and cryptographic replay/provenance digests rather than raw private identifiers.

The engineering bottleneck is real lawful evidence, not another parser or synthetic metric.

## Controlled evaluation checkpoint

Production depth 2 / 12 nodes: 9 labelled admitted pivots (8 relevant, 1 wrong), 11 simulated attempts.

Candidate depth 3 / 12 nodes: 12 labelled admitted pivots (8 relevant, 4 wrong), 14 simulated attempts.

Controlled delta: +3 attempts, +3 wrong-labelled pivots, +0 relevant pivots. This is synthetic regression evidence only; production remains depth 2 / 12 nodes.

Controlled M5 omission results remain diagnostic only. `hard_contradiction` remains a production veto, M5 remains uncalibrated evidence-strength triage and `is_identity_claim=false` remains fixed.

## Permanent boundaries

- Required operation remains zero paid APIs, zero paid database, zero paid hosting requirement, zero paid proxy network and zero paid enrichment.
- Planned/review/manual/reference sources remain non-executable.
- Uploaded content is untrusted data; extraction is never execution authority.
- No private-account bypass, account-recovery enumeration, password/OTP/session/token collection, CAPTCHA/WAF/proxy/Tor evasion, hidden KYC/government-ID acquisition, covert personal/device IP discovery, live tracking, covert subject contact or regulated eligibility decisioning.

## Next gate

1. Put the pivot evidence-context branch through exact-head CI. Repair regressions rather than weakening canonical-reference validation.
2. Merge only when API 3.11/3.13, audits/Ruff, web and production-image checks pass; then record the exact tested checkpoint in this file before merge if the head changes.
3. Prioritize genuine consented or independently reviewed M10 evidence when lawful evidence exists. Do not invent a convenience cohort to claim evaluation progress.
4. Continue operator evidence/provenance work only where it removes a specific investigation step; avoid decorative redesign and duplicated retained evidence.
5. Add another external source only when it materially improves coverage and its current terms/privacy/cost/provenance boundary is defensible.
6. Keep production depth 2 / 12 nodes, M5 uncalibrated/non-probabilistic and `hard_contradiction` active.

## Update discipline

For every meaningful block record verified main/branch/PR state, CI evidence, behavior changes, explicit non-changes, corrected assumptions, unresolved risks and the exact next gate. Keep public/operator prose separate from assistant handover prose.
