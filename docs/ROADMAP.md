# Roadmap

The roadmap is intentionally evidence-first. Social discovery comes after the
data model, upload boundary and provider policy gates, not before them.

## M0 — public foundation

**Status: complete**

- repository, license and source policy
- product architecture
- intake API
- dashboard shell
- CI
- continuity handover

## M1 — evidence core

**Status: complete**

- persistent subject/identifier/observation/claim/evidence-link schemas
- deterministic normalization outside the HTTP layer
- provenance and freshness model
- support/contradict/unresolved evidence relationships
- AI-claim/source-observation separation
- redaction utilities
- synthetic fixtures only

## M2 — safe file intake + extraction boundary

**Status: complete**

- bounded multi-file PDF/TXT upload
- filename, MIME and byte-level validation
- private UUID-named temporary staging and SHA-256 provenance
- isolated text extraction with resource/output ceilings
- upload observations linked by artifact provenance
- deterministic review-only identifier candidates
- explicit human-confirmation gate before any later external query
- prompt-like uploaded content kept inert as untrusted data
- no live AI/provider execution

## M3 — provider framework and governed execution

**Status: complete**

- versioned provider request/result/error contracts
- central purpose/consent/provider-status/contact-risk enforcement immediately
  before execution
- document-derived candidate confirmation and stored-identifier matching
- source/auth/resource metadata in the provider registry
- bounded retry classification, per-attempt local rate budgets, semaphore
  concurrency, timeouts and response-size ceilings
- server-side secret resolution with no credential field in execution requests
- public-safe provider-log redaction helper
- provenance-bearing provider observations in the M1 evidence store
- synthetic no-network adapter as the first executable provider
- explicit deterministic tests for timeout and concurrency controls

During review, a rate-budget flaw was caught before merge: retries initially
consumed the local budget only once per high-level execution. The final design
counts every actual adapter attempt. A second review pass added explicit timeout
and concurrency tests rather than accepting indirect coverage.

## M4 — governed username and public-account discovery

**Status: complete**

- published Sherlock 0.16.0 pinned as the first username verifier
- Sherlock's packaged data is filtered to an eight-site reviewed allowlist;
  no upstream data is copied into this repository
- live manifest/exclusions loading is bypassed
- synchronous Sherlock execution is isolated in a killable child process
- parent/worker IPC carries only approved site names, never arbitrary URLs
- only username identifiers are accepted, enforced centrally by M3
- positive/negative/unknown/illegal/WAF states remain explicit observations
- account hits are candidates, never identity claims
- username log redaction added
- no proxies, Tor/I2P, CAPTCHA/WAF bypass, browser opening, login/cookies or
  private-account access
- Maigret 0.6.3 remains a non-executable enrichment candidate with recursion,
  AI, auto-update and broad scanning disabled by design

Review corrected three assumptions before closure: the repository-declared
Sherlock 0.16.1 was not published on the package index, caller-supplied site
metadata would have made the worker boundary too broad, and one duplicate-result
test fixture triggered the site-count guard before the duplicate guard. The
final implementation pins published 0.16.0, passes only approved site names to
the worker, and tests duplicate rejection inside the configured result budget.

## M5 — explainable evidence correlation engine

**Status: complete**

- deterministic candidate correlation over already-stored evidence only
- dedicated correlation run/factor records, separate from factual claims
- versioned factor weights/thresholds and explicit contradiction/veto rules
- source-independence groups derived from stored provider/source-host provenance
  rather than supplied by callers
- every non-username factor requires supporting source evidence explicitly bound
  to the candidate observation
- exact confirmed identifier overlap requires candidate-bound source evidence
  that records the confirmed non-username identifier IDs
- stale observations remain visible but contribute zero in the initial policy
- same-handle reuse alone remains insufficient evidence
- canonical input/output digests and replay-safe persistence
- explainable triage outcomes rather than automatic identity claims
- every result remains `uncalibrated` and `is_identity_claim=false`
- no external provider calls in the correlation engine
- no AI/ML/biometric matching in the decision path

Review caught a material weakness before merge: the initial draft allowed the
caller to name an evidence independence group. That would have allowed the same
source to be relabelled into multiple groups and inflate evidence. The final
engine derives the group from stored provenance. The same review tightened
strong-factor binding so a subject-level identifier cannot be counted as proof
about a candidate account without a candidate-bound source observation.

Host/provider provenance is still only a conservative independence proxy, not
proof that differently hosted sources are genuinely independent. The policy
keeps that limitation explicit rather than representing the rule score as a
probability.

The earlier phrase "calibrated confidence bands" was intentionally rejected.
A heuristic evidence score is not an identity probability without an appropriate
labelled evaluation and demonstrated calibration.

## M6 — local evidence intelligence dashboard

**Status: complete**

- bounded typed read model for a single case without a stored-case HTTP read
  endpoint;
- static `/dashboard` route backed only by synthetic fixtures;
- case summary, normalized identifiers, source timeline, factual Claims,
  account candidates, M5 factor breakdown, provenance, freshness and visible
  contradiction/stale-evidence states;
- complete, no-evidence, empty, loading and fail-closed error states;
- M5 evidence score is labelled as an uncalibrated rule score and never shown as
  an identity probability;
- claim confidence remains visually and semantically distinct from M5 triage;
- keyboard focus and semantic structure verified on the PC/laptop operator
  target;
- local Next.js development configuration hardened so framework-generated files
  no longer dirty Git;
- Node 24 pinned through `.nvmrc`, `package-lock.json` committed and CI switched
  to reproducible `npm ci` installs;
- no unauthenticated stored-case read/list route, real-case export, AI identity
  decision, biometric matching or autonomous provider expansion.

M6 is intentionally an operator information-architecture and safety milestone,
not the final commercial UI. Tablet/mobile product optimization is not an M6
closure gate; future workflow evidence may justify it later.

## M7 — identity, tenancy and authorization foundation

**Status: next**

- production authentication and session security;
- explicit tenant/owner boundaries for cases and evidence objects;
- object-level and function-level authorization with deny-by-default policy;
- authorization tests for cross-user, cross-tenant and privilege-boundary cases;
- no production stored-case endpoint until these controls are enforced together.

M7 deliberately separates authorization from the rest of production hardening.
Authentication alone is not enough to safely expose identity case objects.

## M8 — privacy lifecycle and governance

- purpose and policy records that are enforceable rather than decorative;
- retention schedules and deletion workflows;
- audit events for sensitive access and policy changes;
- data-minimization and response-field allowlists;
- jurisdiction/purpose policy hooks and documented review boundaries;
- abuse-control policy for stalking, harassment, doxxing and other misuse risks.

## M9 — production case platform

- authenticated and authorized real-case access only after M7/M8 controls exist;
- controlled provider execution from case workflows;
- production evidence views and operator triage;
- export/share capabilities only under explicit access, retention and audit
  policy;
- multi-user collaboration only after tenant isolation is proven.

## M10 — evaluation and calibration laboratory

- consented/synthetic labelled evaluation datasets;
- deterministic replay suites and factor ablation studies;
- false-positive/false-negative and threshold analysis;
- calibration research kept separate from production identity claims;
- no marketing or UI probability claim unless evaluation evidence supports it.

## M11 — provider and cost intelligence

- provider reliability, coverage, latency and failure-characteristic tracking;
- licensing/allowed-purpose/retention restrictions alongside each provider;
- per-query and per-case cost attribution;
- query budgets, spend ceilings and cost-aware orchestration;
- paid-provider expansion only when unit economics and governance are explicit.

## M12 — enterprise evidence integrity

- policy-controlled evidence preservation rather than indiscriminate capture;
- acquisition metadata, integrity hashes and reproducibility records;
- clear separation between original observation and derived interpretation;
- controlled evidence export and chain-of-custody-style auditability where the
  workflow requires it;
- retention/licensing/copyright constraints designed before broad archival
  capture.

## Deferred

Employment, housing, credit or insurance eligibility decisions remain deferred
until the applicable regulatory/compliance obligations have been designed and
reviewed.
