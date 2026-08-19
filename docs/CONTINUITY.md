# Continuity

Public-safe engineering handover for PersonaLattice. Verify GitHub before changing anything; this file is a checkpoint, not authority over the repository.

Never place API keys, real research identifiers, retained-case data, password hashes, session material, raw consent evidence or unredacted investigation screenshots here.

## Repository checkpoint

- Repository: `tushar-rawat-22/persona-lattice`
- Default branch: `main`
- Local checkout convention: `~/persona-lattice`
- License: Apache-2.0 for original code
- Operating model: one authenticated operator; public route is demo/preview only
- PR #136: canonical DOMAIN reachability — merged at `ca2510776e82cb1d795f958355e48551f78fcaa0`
- PR #137: governed metadata-only RDAP activation — activation implementation reviewed on branch `rdap-governed-activation`
- Exact clean implementation head before activation docs: `e1f4d7fa5cfd1d91c1b0640ab1826ba00227be3a`
- Exact-head CI for clean implementation: run `32291601067`, conclusion SUCCESS
- Issue #133: close after PR #137 merges; its DOMAIN and routing-accounting blockers are satisfied by PRs #136/#134 and the activation branch
- Relevant RDAP ADRs: `0069-rdap-domain-admission-preflight.md` through `0076-rdap-governed-runtime-activation.md`
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
- RDAP: explicit DOMAIN reachability is merged; PR #137 activates the metadata-only authoritative provider through the governed runtime.
- Gravatar: admission preflight complete; still PLANNED because its provider-terms/privacy-policy and free server-side-key gate is unresolved.
- WebFinger: parser/admission, SSRF transport, URL-only semantics and exact-host policy are complete; still PLANNED because no concrete host has passed the exact-host source-policy gate.
- M10: deterministic replay, source/graph accounting, real-engine factor ablations, label-provenance manifests and consented-only accounting exist. Representative consented evaluation/calibration remains incomplete.

## PR #137 — governed RDAP activation

The activation is intentionally narrow. It does not add registrant/contact harvesting, WHOIS fallback, RDRS access, reverse lookup, bulk enumeration or automatic domain recursion.

The live path is:

`explicit DOMAIN seed → M1 DOMAIN normalization → rdap_domain_registry binding → DEVELOPMENT provider descriptor → process-wide ProviderRuntime → process-wide IANA bootstrap cache → SSRF-safe authoritative RDAP transport → metadata-only observation → typed source-run report → canonical converged evidence`

The source catalog marks RDAP ACTIVE, reviewed, credentialless and zero-direct-cost. The provider descriptor accepts DOMAIN only. `rdap_domain_registry.emits` stays empty, so the source does not create person/name/email/phone/organization/location leads.

The admitted observation retains only:

- canonical queried domain;
- bounded status values;
- bounded nameserver context;
- explicit registration-context/non-identity/redaction flags;
- validated final HTTPS response locator as evidence provenance.

Registrant/contact names, organizations, addresses, email addresses and telephone numbers are excluded even when an upstream RDAP response contains them.

## Attempt accounting

`routing_unavailable` remains a non-attempt outcome. If the IANA bootstrap cache cannot provide usable current routing authority, no authoritative RDAP service is blamed and provider-attempt/failure counters do not increase.

After an authoritative RDAP service has actually been contacted, remote rate limit, transient service failure and malformed returned result use the existing attempted-failure semantics. A valid not-found response is a completed zero-observation result.

The local ProviderRuntime budget guards the whole application path. It is an application safety control, not a claim about one universal RDAP upstream quota.

## Review corrections made before merge

PR #137 was not accepted merely because its first corrected test head turned green.

The first activation CI run failed because several existing tests still asserted that RDAP was PLANNED/unbound, and one DOMAIN test accidentally depended on live IANA/RDAP availability. The stale expectations were updated to the post-activation contract and the DOMAIN test was made deterministic with an injected unavailable-bootstrap cache.

A separate adversarial diff review then found broad formatting/comment deletion in `research.py`, `source_catalog.py` and `source_bindings.py`. That churn was unrelated to activation and made the PR harder to audit. It was removed before merge. The cleaned activation diff is limited to the provider/runtime/source-state wiring, DOMAIN research behavior, deterministic activation tests and synchronized docs.

The clean implementation head `e1f4d7fa5cfd1d91c1b0640ab1826ba00227be3a` passed CI run `32291601067` completely before ADR/roadmap/continuity were added.

## DOMAIN behavior remains bounded

`IdentifierKind.DOMAIN`, `LeadKind.DOMAIN`, `ResearchKind.DOMAIN`, RDAP admission and live M5 share the same M1 normalization authority.

Explicit domain seeds are executable. Discovered domain clues remain `DISPLAY_ONLY`; activating RDAP does not make domains discovered from an email, URL, profile or other provider observation automatically recurse.

Existing persistent SQLite databases created before DOMAIN was added to the M1 enum constraint may require deliberate recreation/migration before persisting DOMAIN identifiers. The ephemeral live M5 graph is covered by the end-to-end DOMAIN tests.

## Current controlled evaluation checkpoint

Production depth 2 / 12 nodes: 9 labelled admitted pivots (8 relevant, 1 wrong), 11 simulated attempts and 11 request-cost units.

Candidate depth 3 / 12 nodes: 12 labelled admitted pivots (8 relevant, 4 wrong), 14 attempts and 14 request-cost units.

Controlled delta depth 2 → 3: +3 attempts, +3 wrong-labelled pivots and +0 relevant pivots. This is synthetic regression evidence only; production remains depth 2 / 12 nodes.

Controlled M5 omission results remain diagnostic only. `hard_contradiction` remains a production veto, M5 remains uncalibrated evidence-strength triage and `is_identity_claim=false` remains fixed.

## Permanent boundaries

- Required operation remains zero paid APIs, zero paid database, zero paid hosting requirement, zero paid proxy network and zero paid enrichment.
- Planned/review/manual/reference sources remain non-executable.
- Uploaded content is untrusted data; extraction is never execution authority.
- No private-account bypass, account-recovery enumeration, password/OTP/session/token collection, CAPTCHA/WAF/proxy/Tor evasion, hidden KYC/government-ID acquisition, covert personal/device IP discovery, live tracking, covert subject contact or regulated eligibility decisioning.

## Next gate after RDAP activation

Do not add another source merely to increase provider count.

1. Close Issue #133 after PR #137 merges and verify the merge/main CI checkpoint.
2. For M10, prioritize genuinely consented or independently reviewed label evidence. Synthetic regression fixtures must not be relabelled as consented/calibration data.
3. For source expansion, pick only a high-value zero-spend source whose current primary terms/privacy/authentication/provenance model can be defended. Gravatar remains blocked by its privacy-policy/free-key requirements; WebFinger remains blocked until a concrete host passes the exact-host policy gate; ActivityPub actor fetching remains separate and unapproved.
4. Keep production recursion at depth 2 / 12 nodes unless labelled evaluation supports a change.
5. Keep public/operator UI and documentation product-specific and maintainable; do not replace evidence/provenance hierarchy with generic AI-SaaS presentation patterns.

## Update discipline

For every meaningful block record verified main/branch/PR state, CI evidence, behavior changes, explicit non-changes, corrected assumptions, unresolved risks and the exact next gate. Keep public/operator prose separate from assistant handover prose.
