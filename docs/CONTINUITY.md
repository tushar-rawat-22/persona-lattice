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
- Main before PR #121: `b8e5ca32e797c00bdca82ea2d909b7222e761dde`
- PR #121: WebFinger exact-host source-policy gate; no network activation
- Exact tested PR #121 head: `e8d756676a66af534812052c770de32fbed11fa8`
- Exact-head CI: run `32248259706`; API 3.11 PASS, API 3.13 PASS, web PASS, deployment-image PASS
- PR #121 merge: `86b1d03f803bdcd3a8a302c8edefc0eea73db1db`
- Relevant ADRs: `0065-webfinger-admission-preflight.md`, `0066-webfinger-ssrf-transport.md`, `0067-webfinger-url-only-source-contract.md`, `0068-webfinger-exact-host-policy.md`
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
- Gravatar: admission preflight complete in PR #113 / ADR 0064; still PLANNED, unbound and non-recursive because the provider-terms/privacy-policy gate is not satisfied.
- WebFinger: admission preflight PR #115 / ADR 0065; DNS/redirect SSRF transport PR #117 / ADR 0066; URL-only source semantics PR #119 / ADR 0067; exact-host policy gate PR #121 / ADR 0068. Still PLANNED, unbound and non-recursive. ActivityPub actor fetching remains unapproved.
- M10: deterministic source-state fixtures, graph-limit comparison, multi-kind synthetic cohorts, attempt/yield/request-cost accounting, replay fingerprints, real-engine factor ablations, UUID-independent controlled M5 replay, label-provenance manifests and consented-only scenario accounting are implemented. Representative consented evaluation and calibration remain incomplete.

## Latest block — WebFinger exact-host policy gate

Fresh RFC 7033 review confirmed that protocol conformance, valid HTTPS syntax and globally routable DNS are not enough to treat an arbitrary WebFinger host as a reviewed source. RFC 7033 permits WebFinger resources to require authentication and to vary responses by client or network context. Independent fediverse servers can also have different operators and local policies.

PR #121 therefore adds a separate source-policy layer:

- approvals are for one lowercase hostname exactly;
- wildcard approvals are forbidden;
- every approval has an explicit review date, expiry date and concrete rationale;
- sibling hosts and subdomains receive no implied approval;
- future-dated, expired or duplicate approvals fail closed;
- malformed profile URLs fail at the existing URL-admission boundary before policy matching;
- the production approved-host registry is intentionally empty until a real host passes a current primary-source review.

This block does **not** activate WebFinger. There is still no provider registry entry, executable source binding, shared runtime owner or quick-research call for `webfinger_activitypub`.

### Why the production host registry is empty

The next source-policy decision must be about a real server, not an invented fixture. A host should only be added after current primary terms/privacy/source documentation supports unauthenticated public WebFinger use for PersonaLattice's bounded research purpose. The review must be explicit about any local rate, attribution, retention or access-control obligations.

Do not shortcut this by approving `*.example`, all Mastodon servers, all ActivityPub servers or every host that happens to expose `/.well-known/webfinger`.

## Existing WebFinger transport invariants

- explicit profile seeds and retained JRD links use HTTPS;
- ASCII whitespace/control characters are rejected before URL parsing;
- credentials, explicit ports, fragments, IP literals and local-use/single-label hosts are rejected;
- every initial/redirect host is freshly resolved immediately before I/O;
- malformed or non-global resolver output fails closed;
- TCP is pinned to an admitted IP while TLS validation remains bound to the DNS hostname;
- redirects are manual, HTTPS-only, revalidated per hop and capped at three;
- response bodies are bounded to 64 KiB;
- 404, remote rate limit, transient failure and malformed returned behavior remain distinct;
- a post-contact unsafe redirect is malformed returned provider behavior, not a pre-contact policy stop.

The transport is still pre-activation infrastructure. It is not execution authority by itself.

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

The required baseline must work with zero paid APIs, zero paid database, zero paid hosting requirement, zero paid proxy network and zero paid enrichment. Metered integrations can exist only as optional extensions. Brave remains optional/metered. Bluesky requires no paid service. WebFinger remains non-executable.

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
- WebFinger remains planned and cannot execute;
- ActivityPub actor fetching is not approved;
- no identity probability or universal-account claims.

## Next gate

Do not reopen V2-D architecture casually. Do not raise production recursion from synthetic evidence, and do not treat the hard-contradiction ablation as a production recommendation.

M10's highest-value unresolved need remains real label evidence: a genuinely consented or otherwise independently reviewed cohort whose external evidence records satisfy the existing provenance contract. Do not relabel regression fixtures as consented to manufacture progress, and do not call current count fractions false-positive/false-negative rates until cohort design supports that terminology.

For WebFinger, the protocol parser, URL-only semantic contract, SSRF-safe transport and exact-host policy mechanism are complete. The next source-expansion block is to review **one concrete host** using current primary terms/privacy/source documentation. If the host passes, add that exact host approval and then activate WebFinger atomically across source catalog, binding, provider registry, shared `ProviderRuntime`, quick research, typed source-state reporting and canonical evidence. If no host passes, leave WebFinger planned and move to another zero-spend source such as RDAP rather than weakening the gate.

Gravatar remains blocked on its privacy-policy requirement. ActivityPub actor fetching remains separate and unapproved.

## Update discipline

For every meaningful block record verified main/branch/PR state, CI evidence, behavior changes, explicit non-changes, corrected assumptions, unresolved risks and the exact next gate. Keep public/operator prose separate from assistant handover prose.
