# Roadmap

PersonaLattice is an evidence-first private research workbench. The public route
is a product/demo surface; real intake, provider execution and retained case data
belong to one authenticated operator account unless a future security/privacy
review explicitly changes that model.

## Permanent product rules

- Observations, factual Claims and correlation results remain separate.
- Every lead and conclusion keeps provenance.
- A lead is a research direction, not proof of identity.
- Same-handle reuse alone remains insufficient evidence.
- M5 remains uncalibrated evidence-strength triage, not identity probability.
- Contradictions/vetoes and stale evidence remain visible.
- No AI/ML/embedding/biometric identity decision is authorized by the current
  roadmap.
- No private-account bypass, credential/account-recovery enumeration, hidden
  KYC/government-ID acquisition, covert personal/device IP discovery or live
  tracking is a product capability.
- The default product must remain usable without paid APIs, paid hosting, paid
  databases, paid proxies or paid enrichment.

## M0 — public foundation

**Status: complete**

Repository, license/source policy, product architecture, intake API, web shell,
CI and continuity process.

## M1 — evidence core

**Status: complete**

Persistent subject/identifier/observation/claim/evidence-link schemas,
conservative deterministic normalization, provenance/freshness, evidence
relationships, redaction and synthetic fixtures.

## M2 — safe file intake + extraction boundary

**Status: complete**

Bounded PDF/TXT upload plus later private-V1 JPEG/PNG handling, private temporary
staging, resource/output ceilings, untrusted-content treatment and human-review
identifier candidates.

## M3 — governed provider framework

**Status: complete**

Versioned provider contracts, purpose/consent/source/contact-risk gates,
server-side secrets, bounded retries/rate/concurrency/timeout/response ceilings
and provenance-bearing provider observations.

## M4 — governed username/public-account discovery

**Status: complete**

Pinned Sherlock 0.16.0 with a reviewed site subset, killable execution and
explicit account-candidate semantics. No proxy/Tor/CAPTCHA/login/private-profile
bypass.

## M5 — explainable evidence correlation

**Status: complete**

Deterministic correlation, explicit factor vocabulary, provenance-derived
independence groups, contradiction vetoes, stale evidence at zero contribution,
replay-safe digests and persisted factor/run records.

Permanent outputs remain:

- `calibration_status=uncalibrated`
- `is_identity_claim=false`

## M6 — local evidence intelligence dashboard

**Status: complete**

Bounded read model, synthetic dashboard states, provenance/freshness/claims/
candidates/factors/contradictions/stale evidence, PC/laptop keyboard review and
reproducible Node 24/lockfile/`npm ci` toolchain.

## M7 — private one-admin live research product

**Status: implemented and manually accepted locally**

Implemented:

- one deployment-configured admin identity;
- Argon2 password verification;
- opaque HttpOnly sessions, logout/revocation and CSRF protection;
- public demo route separated from private `/admin`;
- same-origin Next.js `/api` proxy;
- authenticated real intake/research;
- GitHub, GitLab and Codeforces public-profile enrichment;
- reviewed Sherlock username discovery;
- phone numbering-plan/carrier/region/time-zone metadata;
- exact public-email/public-web paths where configured;
- retained private cases.

Manual acceptance has succeeded through a local public HTTPS tunnel with the web
service on port 3000 and API bound locally on port 8000. This proves the private
operator path but is not durable hosting.

## M8 — privacy lifecycle, audit and source expansion

**Status: substantially implemented in private V1**

Implemented:

- automatic expiry purge and explicit delete workflows;
- privacy-safe audit events;
- 30-day default retained-case lifecycle;
- secrets outside Git;
- optional licensed exact-public-web search;
- bounded source/resource budgets.

Remaining operational work:

- prefer local/self-hosted operation unless durable free hosting materially
  improves the operator workflow;
- define backup/restore after a persistent production store actually exists;
- keep measuring provider reliability and cost before any optional metered
  enrichment is considered.

## M9 — evidence graph and report convergence

**Status: private V1 implemented; V2 architecture now extends it**

Private V1 already admits live provider evidence into an ephemeral canonical M1
graph, runs M5 and retains only the bounded report/provenance decision record.
This deliberately avoids a second persistent raw-personal-data graph.

The V2 work below makes recursive lead generation and source planning explicit.

## V2-A — typed recursive evidence lead graph

**Status: complete — PR #20**

Merge commit: `e66944259c545cdfe8e4020312357b92a42911ba`.

Implemented:

- typed lead kinds: username, email, phone, URL, domain, name, organization,
  location;
- dispositions: automatic pivot, review-required, display-only, blocked;
- exact-field allowlisted lead extraction;
- M1 normalization reused as the generic comparison authority;
- newly discovered phone leads require review;
- name/org/location context does not silently fan out;
- government-ID, credential/token and personal/device-IP values are blocked from
  recursive lead state;
- generic username/email case semantics corrected to match M1;
- ADR 0010 and `V2_SOURCE_EXPANSION_PLAN.md`.

## V2-B — deterministic frontier orchestration

**Status: complete — PR #21**

Merge commit: `2a69224e53ea1912879032548a38f017bfcafb6a`.
Post-merge CI `31974590505`: success.

Implemented:

- reservation-safe `LeadFrontier`;
- duplicate/cycle suppression;
- reason-coded final states (`admitted`, `provider_failed`, `duplicate`, review/
  display and budget stops);
- duplicate clue origins retain provenance while provider execution remains
  deduplicated;
- provider failure releases capacity;
- additive `lead_graph` report state;
- current V1 depth/node limits preserved;
- ADR 0011.

Current hard ceilings remain depth 2 / 12 nodes. Raising them is an evaluation
question, not a feature checkbox.

## V2-C — source capability registry and planner

**Status: complete — PR #22**

Merge commit: `b1192fd15d73c144faba6279559db3e2b6ae2980`.
Post-merge CI `31974993479`: API 3.11 PASS, API 3.13 PASS, web PASS,
deployment-image PASS.

Implemented:

- source capability catalog separated from execution authority;
- accepted/emitted lead kinds;
- active/optional/review/manual/reference/planned lifecycle state;
- source mode, broad cost class, credential class and source-policy review state;
- recursive eligibility invariant;
- zero-spend-aware non-executing source plans;
- active/optional/deferred/planned/budget-excluded buckets;
- consistency tests against the existing governed provider registry;
- future integration targets catalogued but non-executable: Bluesky, Gravatar,
  WebFinger/ActivityPub, RDAP and user-authorized Google People;
- ADR 0012.

A source appearing in the catalog is never permission to call it.

## V2-D — source-adapter/runtime consistency

**Status: active; current-provider migration substantially complete**

The original source-adapter gate is no longer future work. PRs #24 through #32
have already established the binding/runtime boundary and migrated the current
zero-direct-cost network sources onto the shared governed runtime.

Completed:

- PR #24: catalog-to-runtime source binding admission;
- PR #25: storage-independent `ProviderRuntime` extraction;
- PR #26: Sherlock quick research moved to the governed runtime;
- PR #27: GitHub public-profile runtime migration;
- PR #28: GitHub rate-budget/regression repair;
- PR #29: one process-wide production provider runtime;
- PR #30: GitLab username and exact-public-email runtime migration;
- PR #31: Codeforces runtime migration and corrected request budget;
- PR #32: public DNS runtime migration with infrastructure-only IP semantics;
- typed source-run state/reason contract for `executed`, `not_found`, `queued`,
  `review_required`, `display_only`, `blocked`, `unavailable` and
  `budget_stopped` outcomes.

Remaining before V2-D closes:

1. wire typed source-run records into convergence/retained reports and synthetic
   deterministic fixtures;
2. migrate the existing optional Brave exact-match search behind
   `ProviderRuntime` while keeping it outside the zero-spend baseline;
3. remove the final legacy network execution allowance;
4. finish document-candidate-to-reviewed-lead plumbing and source-state UI/report
   exposure;
5. run consistency/failure-path evaluation before activating any new network
   provider.

No new third-party source should be activated during these closure blocks.

## M10 — evaluation and calibration laboratory

**Status: follows V2-D architecture closure**

Before increasing recursion limits or changing correlation thresholds:

- synthetic/consented labelled graph fixtures;
- wrong-pivot, duplicate and source-failure measurements;
- graph-growth and cost-per-seed measurements;
- deterministic replay/factor ablations;
- false-positive/false-negative and threshold analysis;
- no probability claim unless calibration evidence actually supports it.

## Immediate next gate

Integrate the typed source-run contract into retained convergence/report output
and deterministic fixtures. Then migrate optional Brave behind the shared runtime
without making it a baseline dependency.

After V2-D closes, new public/API sources may be reviewed one at a time. Each
activation must re-check current official terms, authentication, limits and cost;
old roadmap pricing notes are not authority.

Success means a small clue can grow into a broad evidence graph while the
operator can answer for every hop:

> What source produced this clue, why was it allowed to become a lead, what did
> the system do with it, and what remains unknown?
