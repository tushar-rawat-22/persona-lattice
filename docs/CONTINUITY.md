# Continuity

Public-safe engineering handover for PersonaLattice. Verify GitHub before changing anything; this file is a checkpoint, not authority over the repository.

Never place API keys, real research identifiers, retained-case data, password hashes, session material, raw consent evidence or unredacted investigation screenshots here.

## Repository checkpoint

- Repository: `tushar-rawat-22/persona-lattice`
- Default branch: `main`
- Local checkout convention: `~/persona-lattice`
- License: Apache-2.0 for original code
- Product: private evidence-first public/authorized research workbench
- Operating model: one authenticated operator; public route is demo/preview only
- Main before PR #113: `0aefa13a552d0704f65b535acf57d391bac17565`
- PR #113: Gravatar admission preflight; source remains non-executable
- Exact tested PR #113 head: `760936e9ee7a84cc4e65b4f14783936053e90747`
- Exact-head CI: run `32228479066`, full success across API 3.11/3.13, dependency checks/audits, Ruff, web audit/lint/typecheck/build and production API image
- PR #113 merge: `abe08b033f52ecb047d2c31e739e0efb955c110f`
- ADR: `docs/decisions/0064-gravatar-admission-preflight.md`
- Documentation standard: `docs/DOCUMENTATION_STANDARD.md`
- Zero-spend runbook: `docs/ZERO_SPEND_RUNBOOK.md`
- Optional paid Render reference: `deploy/render-paid.yaml`

## Milestone state

- M0-M6: complete.
- M7 private one-admin product: implemented and manually accepted locally.
- M8 privacy lifecycle/operations: substantially implemented; hosted backup/restore remains deferred until a persistent hosted store is selected.
- M9 private convergence: implemented.
- V2-A typed lead graph: complete, PR #20.
- V2-B deterministic frontier: complete, PR #21.
- V2-C source capability registry/planner: complete, PR #22.
- V2-D runtime consistency and architecture closure: complete, PRs #89-#90, ADRs 0050-0051.
- Post-V2-D source expansion: Bluesky public profiles active for valid AT handles through the governed runtime, PR #98 / ADR 0055.
- Gravatar: admission preflight complete in PR #113 / ADR 0064; still PLANNED, unbound and non-recursive.
- M10: deterministic source-state fixtures, graph-limit comparison, multi-kind synthetic cohorts, attempt/yield/request-cost accounting, replay fingerprints, real-engine factor ablations, UUID-independent controlled M5 fixture replay, label-provenance manifests and consented-only scenario accounting are implemented. Representative consented evaluation and calibration remain incomplete.

## Latest block — Gravatar admission preflight

Fresh official review established that Gravatar's Profiles API uses a SHA-256 identifier derived from a trimmed, lower-cased email. The Profiles API is currently free; Gravatar recommends a server-side API key for production use and documents higher limits for authenticated calls.

The upstream profile schema exposes substantially more data than PersonaLattice needs, including location, company, verified accounts, contact information, payment information, biography, image URLs and other profile fields. PR #113 therefore adds only a local admission boundary:

- `services/api/app/providers/gravatar_admission.py`;
- provider-local email hash derivation only; canonical PersonaLattice email normalization is unchanged;
- returned profile hash must exactly match the requested email-derived hash;
- canonical provenance must be HTTPS `gravatar.com/<slug>` with no credentials, port, query or fragment;
- retained payload is limited to optional display name plus `account_candidate=true`, `identity_claim=false` and public-profile visibility metadata;
- broader Gravatar fields are not admitted;
- deterministic malformed, mismatch and provenance tests are included;
- there is no network request, provider registry entry, source binding, shared-runtime owner or API key in this block.

### Activation blocker

Automattic's current API terms require an application using its APIs to disclose how API data is collected/stored/refreshed and to provide an accessible privacy policy. PersonaLattice currently has no privacy-policy surface. Activating Gravatar before that requirement is satisfied would be a provider-terms defect.

A future activation must therefore re-check current official terms and must not proceed until:

1. PersonaLattice exposes an accurate accessible privacy policy/disclosure;
2. a free server-side Gravatar key is configured outside Git without creating a paid baseline dependency;
3. source catalog, binding, provider registry, shared `ProviderRuntime`, quick research and typed source-run reporting are activated atomically;
4. success, not-found, missing-key, malformed-result, rate-limit and unavailable behavior are deterministically tested;
5. the retained field set remains minimal.

Do not turn this into a universal email-account existence checker and do not add avatar, contact, payment, biography or verified-account harvesting as part of activation.

## Current controlled synthetic graph result

Production policy — depth 2 / 12 nodes:

- 6 synthetic fixtures;
- 9 labelled admitted pivots: 8 relevant, 1 wrong;
- 11 simulated source attempts;
- 9 successful/yield-producing attempts;
- 2 zero-yield provider failures;
- 11 abstract request-cost units;
- 9 observation-yield units;
- 3 local budget stops.

Candidate depth 3 / 12 nodes:

- 12 labelled admitted pivots: 8 relevant, 4 wrong;
- 14 simulated source attempts;
- 12 successful/yield-producing attempts;
- 2 zero-yield provider failures;
- 14 abstract request-cost units;
- 12 observation-yield units;
- no depth budget stops.

Delta depth 2 → depth 3: +3 attempts, +3 request-cost units, +3 yield units, +3 wrong-labelled pivots and +0 relevant pivots in this synthetic cohort. This is regression evidence only. Production recursion remains depth 2 / 12 nodes.

## Current controlled M5 sensitivity result

Under `m5-evidence-strength-v1`:

- metadata/temporal: baseline `possible_match`, score 35; omit compatible profile metadata → `insufficient_evidence`, score 20 (`-15`);
- exact identifier: baseline `strong_candidate`, score 75; omit exact confirmed identifier overlap → `insufficient_evidence`, score 20 (`-55`);
- independent cross-link: baseline `strong_candidate`, score 70; omit independent cross-link → `possible_match`, score 35 (`-35`);
- contradiction veto: baseline `contradicted`, score 0; diagnostic omit hard contradiction → `strong_candidate`, score 90 (`+90`).

The contradiction omission is safety-critical diagnostic work only. No M5 factor weight, threshold, veto, calibration status or identity semantic changed.

## Permanent evidence semantics

- Observations, factual Claims and correlation results remain separate.
- Every factual conclusion keeps provenance.
- A discovered clue is a research lead, not proof of identity.
- Same-handle reuse alone is weak evidence.
- M5 is deterministic evidence-strength triage, not identity probability.
- `calibration_status=uncalibrated` and `is_identity_claim=false` remain fixed.
- Contradictions/vetoes and stale evidence remain visible.
- Unknown, not-found, withheld, unavailable, blocked and budget-stopped remain distinct outcomes.
- No AI/ML/embedding/biometric identity decision is in the correlation path.

## Permanent security, privacy and cost boundary

Allowed scope is attributable public information and explicitly authorized data. PersonaLattice does not add private-account bypass, login/account-recovery enumeration, password/OTP/session/token collection, CAPTCHA/WAF/proxy/Tor evasion, hidden KYC/government-ID acquisition, covert personal/device IP discovery, live tracking, covert subject contact or regulated eligibility decisioning.

The required baseline must work with zero paid APIs, zero paid database, zero paid hosting requirement, zero paid proxy network and zero paid enrichment. Metered integrations can exist only as optional extensions. Brave remains optional/metered; no `BRAVE_SEARCH_API_KEY` means no Brave attempt. Bluesky requires no credential or paid service. A future Gravatar integration may use a free server-side key, but it must not become a paid baseline dependency.

Uploaded content is untrusted data. Extraction is never execution authority. A candidate becomes externally research-authorized only after explicit human confirmation, and only a separate explicit run action may start research.

## Closed V2-D invariants

Current network execution is governed for Sherlock, GitHub, GitLab, Codeforces, Bluesky (valid AT handles only), public DNS and optional Brave exact-match search. The executable legacy-network allowance is empty.

Catalog, executable binding, provider registry and process-wide runtime ownership are checked symmetrically. Planned/review/manual/reference sources remain non-executable. Required active recursive sources must be zero-spend eligible; a non-zero-spend recursive source can only be optional.

Retained source-run projections carry typed state/reason and bounded count metadata without duplicating identifier values, source locators, provider payloads, secrets, exception text or timing data. Complete provider evidence/provenance has canonical retained owners. Historical formats remain read-only compatible.

Reviewed-document extraction creates candidates only; short-lived server-owned review state owns authorization; review mutation cannot alter candidate value/provenance; promotion does not call providers; only a separate authenticated, CSRF-protected explicit case-run action can begin research.

## Current deliberate limits

- convergence max depth: 2;
- convergence max nodes: 12;
- newly discovered phone leads require review;
- contextual name/organization/location remain non-autonomous;
- public-search snippets do not become automatic identifier leads;
- Brave remains optional and excluded from required zero-spend operation;
- Bluesky is applicable only to syntactically valid AT handles, not arbitrary usernames;
- Gravatar remains planned and cannot execute;
- no identity probability or universal-account claims.

## Next gate

Do not reopen V2-D architecture casually. Do not raise production recursion from synthetic evidence, and do not treat the hard-contradiction ablation as a production recommendation.

The highest-value M10 need remains real label evidence: assemble a genuinely consented or otherwise independently reviewed cohort whose external evidence records satisfy the existing provenance contract. Do not relabel regression fixtures as consented to manufacture progress, and do not call the current count fractions false-positive/false-negative rates until cohort design supports that terminology.

For source expansion, Gravatar activation is blocked until the privacy-policy requirement above is satisfied. A separate acceptable source track is fresh review of exactly one other zero-spend candidate such as WebFinger/ActivityPub or RDAP, with current official terms, cost, authentication, fields, contact risk and retention reviewed before any activation.

## Update discipline

For every meaningful block record verified main/branch/PR state, CI evidence, behavior changes, explicit non-changes, corrected assumptions, unresolved risks and the exact next gate. Keep public/operator prose separate from assistant handover prose.
