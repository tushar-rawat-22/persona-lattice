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
- Main before PR #126: `8935912974703553ee4af15707dd3b2a8c2fe639`
- PR #126: RDAP metadata-only source contract; no network activation
- Exact tested PR #126 head: `d5467790f28753fd34353d198a0763936b4b4353`
- Exact-head CI: run `32259306387`; API 3.11 PASS, API 3.13 PASS, web PASS, deployment-image PASS
- PR #126 merge: `cf6640993306bdf2fbf0e236e7c6682936220388`
- Issue #124: closed by PR #126
- Relevant ADRs: `0065-webfinger-admission-preflight.md`, `0066-webfinger-ssrf-transport.md`, `0067-webfinger-url-only-source-contract.md`, `0068-webfinger-exact-host-policy.md`, `0069-rdap-domain-admission-preflight.md`, `0070-rdap-metadata-only-source-contract.md`
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
- Gravatar: admission preflight complete, PR #113 / ADR 0064; still PLANNED because the provider-terms/privacy-policy gate is not satisfied.
- WebFinger: parser/admission, SSRF transport, URL-only semantics and exact-host policy are complete through PR #121 / ADR 0068; still PLANNED because no concrete host has passed a sufficiently explicit host-specific source-policy review.
- RDAP: admission preflight complete in PR #123 / ADR 0069; metadata-only source contract complete in PR #126 / ADR 0070. It remains PLANNED, unbound, source-policy-unreviewed and non-recursive. No RDAP network request exists.
- M10: deterministic source-state fixtures, graph-limit comparison, multi-kind synthetic cohorts, attempt/yield/request-cost accounting, replay fingerprints, real-engine factor ablations, UUID-independent controlled M5 replay, label-provenance manifests and consented-only scenario accounting are implemented. Representative consented evaluation and calibration remain incomplete.

## Latest block — RDAP metadata-only source contract

PR #123 established the network-free RDAP admission boundary from current IANA/ICANN/RFC material. It accepts explicit bare public domains, derives authoritative service URLs from IANA-style bootstrap data, validates matching RDAP domain responses, retains only bounded status/nameserver registration context and excludes registrant/contact identity fields.

Issue #124 identified an unsafe catalog overclaim: `rdap_domain_registry` declared `LeadKind.ORGANIZATION` emission even though registrar organization is service context and registrant organization can be redacted or semantically ambiguous.

PR #126 closes that blocker:

- `rdap_domain_registry.emits = frozenset()`;
- the source stays PLANNED, source-policy-unreviewed, unbound and non-recursive;
- the retained RDAP fixture contains registrant name, organization, email, telephone and address plus registrar context, and proves none survives the admitted observation;
- the admitted observation is passed through the normal exact-field lead extractor;
- no name/email/phone/organization/location candidate can be produced from the retained RDAP payload;
- the already-known queried `domain` remains visible to the generic extractor only as a `DISPLAY_ONLY` duplicate candidate. It is not treated as a newly emitted autonomous pivot.

### Corrections made during review

Two assumptions were deliberately rejected rather than encoded into tests:

1. The first regression incorrectly required **zero** typed candidates from the admitted observation. Because the observation retains the queried `domain`, the generic extractor correctly creates one display-only domain candidate. The test and ADR were corrected to assert the actual safety property: no registrant/registrar/contact/organization field can become a subject lead.
2. The first exact-head CI run exposed a stale source-catalog test that still required RDAP `ORGANIZATION` emission. That was an old contract assertion, not a reason to restore the unsafe emission. The test was changed to assert metadata-only output, planned/non-recursive status and zero-spend eligibility. The corrected exact head then passed the full CI matrix.

`docs/ROADMAP.md` was also corrected in PR #126: its prior immediate gate still pointed at a WebFinger-host review that had already been attempted. The source-expansion gate now points at the RDAP transport/provider block.

## RDAP transport still required

A syntactically admitted bootstrap URL is not execution authority. Before RDAP can become active, one bounded block must:

- resolve authoritative service location from the IANA DNS bootstrap registry;
- perform fresh DNS/global-address validation immediately before network I/O;
- use bounded HTTPS transport and revalidate every redirect target;
- bound response size;
- distinguish success, not-found, malformed response, remote rate limit and transient unavailability through the typed source-run contract;
- use only data returned by unauthenticated public RDAP;
- connect catalog → binding → provider registry → shared `ProviderRuntime` → quick research → typed source state → canonical observation atomically;
- keep `emits = frozenset()` and the retained metadata-only payload.

No WHOIS fallback, nonpublic RDRS workflow, bulk search, reverse search or contact harvesting is approved.

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

The required baseline must work with zero paid APIs, zero paid database, zero paid hosting requirement, zero paid proxy network and zero paid enrichment. Metered integrations can exist only as optional extensions. Brave remains optional/metered. Bluesky requires no paid service. WebFinger and RDAP remain non-executable.

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
- RDAP remains planned and cannot execute;
- ActivityPub actor fetching is not approved;
- no identity probability or universal-account claims.

## Next gate

Do not reopen V2-D architecture casually. Do not raise production recursion from synthetic evidence, and do not treat the hard-contradiction ablation as a production recommendation.

M10's highest-value unresolved need remains real label evidence: a genuinely consented or otherwise independently reviewed cohort whose external evidence records satisfy the existing provenance contract. Do not relabel regression fixtures as consented to manufacture progress.

For source expansion, the next bounded block is the RDAP authoritative transport/provider path described above. Activate RDAP only if the entire governed path and deterministic fixtures are green while preserving metadata-only semantics and the zero-spend baseline.

WebFinger remains planned unless a concrete host passes the exact-host source-policy gate. Gravatar remains blocked on its privacy-policy requirement. ActivityPub actor fetching remains separate and unapproved.

## Update discipline

For every meaningful block record verified main/branch/PR state, CI evidence, behavior changes, explicit non-changes, corrected assumptions, unresolved risks and the exact next gate. Keep public/operator prose separate from assistant handover prose.
