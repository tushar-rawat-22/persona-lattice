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
- Main before PR #123: `336e0e09ff6590ec241038b7c81aa8611e77e9bc`
- PR #123: RDAP domain admission preflight; no network activation
- Exact tested PR #123 head: `c23a9231a03e67f2ed27145a3ed367eff7c62b29`
- Exact-head CI: run `32253190829`; API 3.11 PASS, API 3.13 PASS, web PASS, deployment-image PASS
- PR #123 merge: `059c93b0b75a10d2992cd5b517747cc8f8338c5a`
- Open blocker: Issue #124 — remove automatic RDAP `ORGANIZATION` emission before activation
- Relevant ADRs: `0065-webfinger-admission-preflight.md`, `0066-webfinger-ssrf-transport.md`, `0067-webfinger-url-only-source-contract.md`, `0068-webfinger-exact-host-policy.md`, `0069-rdap-domain-admission-preflight.md`
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
- WebFinger: parser/admission, SSRF transport, URL-only semantics and exact-host policy are complete through PR #121 / ADR 0068; still PLANNED because no concrete host has yet passed a sufficiently explicit current host-specific source-policy review.
- RDAP: domain admission preflight complete, PR #123 / ADR 0069; still PLANNED, unbound and non-recursive. No RDAP network request exists.
- M10: deterministic source-state fixtures, graph-limit comparison, multi-kind synthetic cohorts, attempt/yield/request-cost accounting, replay fingerprints, real-engine factor ablations, UUID-independent controlled M5 replay, label-provenance manifests and consented-only scenario accounting are implemented. Representative consented evaluation and calibration remain incomplete.

## Latest block — RDAP domain admission preflight

A concrete WebFinger review was attempted against `mastodon.social`. Current primary Mastodon material confirms WebFinger is core public federation infrastructure, but the review did not establish a sufficiently explicit host-specific terms/privacy basis to approve that host under PersonaLattice's exact-host policy. The gate was not weakened. WebFinger remains non-executable.

The fallback source review moved to RDAP. Current primary material supports the following:

- IANA publishes the DNS RDAP bootstrap registry and its protocol-registry data is available under CC0-style terms;
- RFC 9082 defines authoritative RDAP domain queries using the bootstrap base URL plus `domain/<name>`;
- ICANN treats RDAP as the definitive gTLD registration-data source and explicitly supports privacy redaction and differentiated access;
- nonpublic registration data is outside PersonaLattice's public zero-spend baseline.

PR #123 adds a network-free RDAP admission boundary:

- accepts only explicit bare multi-label DNS domain names;
- canonicalizes IDNs to A-label form;
- rejects URLs, credentials, IP literals and local-use names;
- reads only matching IANA-style DNS bootstrap entries;
- accepts HTTPS bootstrap base URLs only and rejects credentials, query/fragment data and non-default ports;
- constructs the RFC 9082 domain query path deterministically;
- requires a returned domain object and matching `ldhName`;
- retains only bounded domain status and nameserver context plus explicit non-identity/redaction metadata;
- excludes registrant/contact names, addresses, email, telephone and organization values;
- treats upstream redaction as authoritative and never attempts to infer or recover omitted data.

RDAP remains PLANNED, unbound and non-recursive. There is no provider registry entry, shared runtime owner or quick-research call.

## RDAP blocker found during review

The existing catalog entry for `rdap_domain_registry` still claims `LeadKind.ORGANIZATION` emission. That is too broad for activation.

- registrar organization describes a registration service, not necessarily the researched subject;
- registrant organization may be redacted;
- even when a registrant organization is published, role/attribution must be reviewed before it can become a recursive subject lead.

Issue #124 tracks the required correction. Before RDAP activation, narrow the source to metadata-only output (`emits = frozenset()`), add a regression proving RDAP organization/contact fields cannot become typed leads, and keep all registrant/contact fields out of the admitted observation payload.

## RDAP transport still required

A syntactically admitted bootstrap URL is not sufficient execution authority. Any future RDAP adapter must:

- resolve authoritative service location from the IANA DNS bootstrap registry;
- use bounded HTTPS transport with fresh DNS/global-address validation before I/O;
- fail closed across redirects and revalidate every network target;
- bound response size;
- distinguish success, not-found, malformed response, remote rate limit and transient unavailability through the typed source-run contract;
- use only data returned by unauthenticated public RDAP;
- add no WHOIS fallback, nonpublic RDRS workflow, bulk search, reverse search or contact harvesting.

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

For source expansion, resolve Issue #124 first: remove RDAP's automatic `ORGANIZATION` emission and lock metadata-only semantics. After that, the next bounded RDAP block should add the SSRF-safe authoritative transport/provider path and deterministic success/not-found/malformed/rate-limit/unavailable fixtures. Only activate RDAP when catalog → binding → provider registry → shared `ProviderRuntime` → quick research → typed source-state → canonical observation agree atomically.

WebFinger remains planned unless a concrete host passes the existing exact-host source-policy gate. Gravatar remains blocked on its privacy-policy requirement. ActivityPub actor fetching remains separate and unapproved.

## Update discipline

For every meaningful block record verified main/branch/PR state, CI evidence, behavior changes, explicit non-changes, corrected assumptions, unresolved risks and the exact next gate. Keep public/operator prose separate from assistant handover prose.
