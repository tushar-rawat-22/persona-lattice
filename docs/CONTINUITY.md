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
- Main before PR #115: `d0d9a0835bc3a97ad400cd088179e1fb411ad8a2`
- PR #115: WebFinger admission preflight; source remains non-executable
- Exact tested PR #115 head: `f1b73e0818ec9561ba85b1775a19e9752a11eb7a`
- Exact-head CI: run `32233384289`, full success across API 3.11/3.13, dependency checks/audits, Ruff, web audit/lint/typecheck/build and production API image
- PR #115 merge: `1e052a48c6551d650c6830fe27063b5e3a04960b`
- ADR: `docs/decisions/0065-webfinger-admission-preflight.md`
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
- Gravatar: admission preflight complete in PR #113 / ADR 0064; still PLANNED, unbound and non-recursive because the provider-terms/privacy-policy gate is not yet satisfied.
- WebFinger/ActivityPub: WebFinger admission preflight complete in PR #115 / ADR 0065; still PLANNED, unbound and non-recursive. ActivityPub actor fetching is not approved by this block.
- M10: deterministic source-state fixtures, graph-limit comparison, multi-kind synthetic cohorts, attempt/yield/request-cost accounting, replay fingerprints, real-engine factor ablations, UUID-independent controlled M5 fixture replay, label-provenance manifests and consented-only scenario accounting are implemented. Representative consented evaluation and calibration remain incomplete.

## Latest block — WebFinger admission preflight

Fresh review used RFC 7033 plus current Mastodon WebFinger documentation. WebFinger is an open HTTPS standard and requires no API credential or paid service. Individual federated servers may still differ in policy and availability.

PR #115 adds only a network-free admission boundary:

- `services/api/app/providers/webfinger_admission.py`;
- only explicit absolute HTTPS profile URLs are accepted as resource seeds;
- credentials, explicit ports, query/fragment seeds, IP literals, single-label/local-use hosts and `/.well-known/` seeds fail closed;
- DNS hostnames are syntactically validated and IDNA-normalized, but this preflight does **not** claim they currently resolve to public IPs;
- the RFC 7033 request endpoint is constructed on the same host as the explicit profile resource;
- returned JRDs must be anchored to the requested profile URL through `subject` or `aliases`;
- only bounded HTTPS `self` and `profile-page` links are admitted;
- query/fragment links, credential-bearing links, explicit-port links, IP-literal links and malformed DNS labels are rejected;
- WebFinger properties are not treated as names or other personal attributes;
- `acct:user@domain` is not collapsed into a generic username lead;
- there is no DNS lookup, network request, provider registry entry, source binding or shared-runtime owner in this block.

### Activation blockers

The existing planned catalog entry `webfinger_activitypub` currently claims it may emit URL, generic USERNAME and NAME leads. That is broader than RFC 7033 alone supports. Converting `acct:alice@example.com` to generic username `alice` discards the federation domain and could cause unsafe cross-service spraying. WebFinger also does not itself establish a display name.

Before activation:

1. narrow the executable WebFinger output contract to URL-only, or split ActivityPub actor fetching into a separately reviewed capability;
2. implement provider/runtime redirect handling that revalidates every redirect target and prevents DNS rebinding/private-network SSRF;
3. resolve the request host immediately before I/O and reject non-global addresses;
4. add deterministic success, not-found, malformed, unavailable/rate-limit and redirect/SSRF fixtures;
5. activate catalog, binding, provider registry, shared `ProviderRuntime`, quick research and typed source-run reporting atomically;
6. keep ActivityPub actor fetching out of the activation unless its own content-type, response-size, payload and retention rules are reviewed.

Do not activate the current combined catalog declaration unchanged.

## Gravatar blocker

Gravatar's preflight remains valid but activation is blocked. Automattic's current API terms require an application using its APIs to disclose how API data is collected/stored/refreshed and to provide an accessible privacy policy. PersonaLattice does not yet provide that surface. A future Gravatar activation also needs a free server-side key outside Git and deterministic provider fixtures. It must remain unnecessary to the zero-spend baseline.

## Current controlled synthetic graph result

Production depth 2 / 12 nodes: 9 labelled admitted pivots (8 relevant, 1 wrong), 11 simulated attempts, 9 yield-producing attempts, 2 zero-yield provider failures, 11 request-cost units, 9 observation-yield units and 3 local budget stops.

Candidate depth 3 / 12 nodes: 12 labelled admitted pivots (8 relevant, 4 wrong), 14 attempts, 12 yield-producing attempts, 2 zero-yield provider failures, 14 request-cost units, 12 observation-yield units and no depth budget stops.

Controlled delta depth 2 → 3: +3 attempts, +3 request-cost units, +3 yield units, +3 wrong-labelled pivots and +0 relevant pivots. This is synthetic regression evidence only. Production recursion remains depth 2 / 12 nodes.

## Current controlled M5 sensitivity result

Under `m5-evidence-strength-v1`:

- compatible profile metadata omission: `possible_match` 35 → `insufficient_evidence` 20;
- exact confirmed identifier omission: `strong_candidate` 75 → `insufficient_evidence` 20;
- independent cross-link omission: `strong_candidate` 70 → `possible_match` 35;
- diagnostic hard-contradiction omission: `contradicted` 0 → `strong_candidate` 90.

The contradiction omission is safety-critical diagnostic work only. No production factor weight, threshold, veto, calibration status or identity semantic changed.

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

The required baseline must work with zero paid APIs, zero paid database, zero paid hosting requirement, zero paid proxy network and zero paid enrichment. Metered integrations can exist only as optional extensions. Brave remains optional/metered. Bluesky and WebFinger require no credential or paid service; WebFinger is still non-executable.

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
- Bluesky applies only to syntactically valid AT handles, not arbitrary usernames;
- Gravatar remains planned and cannot execute;
- WebFinger/ActivityPub remains planned and cannot execute;
- no identity probability or universal-account claims.

## Next gate

Do not reopen V2-D architecture casually. Do not raise production recursion from synthetic evidence, and do not treat the hard-contradiction ablation as a production recommendation.

M10's highest-value unresolved need remains real label evidence: a genuinely consented or otherwise independently reviewed cohort whose external evidence records satisfy the existing provenance contract. Do not relabel regression fixtures as consented to manufacture progress, and do not call current count fractions false-positive/false-negative rates until cohort design supports that terminology.

For source expansion, the next safe WebFinger step is **not** activation-by-status-flip. First correct the catalog/output model and define a redirect/DNS-resolution SSRF boundary. RDAP remains another acceptable zero-spend source-review track. Gravatar remains blocked on its privacy-policy requirement.

## Update discipline

For every meaningful block record verified main/branch/PR state, CI evidence, behavior changes, explicit non-changes, corrected assumptions, unresolved risks and the exact next gate. Keep public/operator prose separate from assistant handover prose.
