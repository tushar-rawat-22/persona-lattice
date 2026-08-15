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
- synthetic no-network adapter as the only executable provider
- explicit deterministic tests for timeout and concurrency controls

During review, a rate-budget flaw was caught before merge: retries initially
consumed the local budget only once per high-level execution. The final design
counts every actual adapter attempt. A second review pass added explicit timeout
and concurrency tests rather than accepting indirect coverage.

## M4 — governed username and public-account discovery

**Status: next — Issue #9**

- integrate Sherlock first as a bounded username-existence verifier
- evaluate Maigret second as constrained enrichment
- pin reviewed upstream versions and preserve MIT attribution boundaries
- require user-supplied or human-confirmed username identifiers
- reuse the M3 execution/policy/resource controls
- persist public account hits as observations/candidates, never identity proof
- retain positive, negative, unknown and contradictory outcomes explicitly
- no proxies, Tor/I2P, CAPTCHA bypass, browser opening, login/cookies or private
  account access
- disable Maigret recursion, AI mode, auto-update and unrestricted all-site scans
  if a Maigret adapter is added

## M5 — correlation engine

- candidate entity graph
- weighted evidence factors
- contradiction penalties
- calibrated confidence bands
- explainable "why this match" output

## M6 — dashboard intelligence

- case timeline
- evidence graph
- missing-data/gap panel
- professional vs personal evidence views
- source freshness and confidence
- exportable report

## M7 — privacy and production hardening

- authentication and authorization
- retention/deletion
- audit log
- abuse controls
- provider contract review
- privacy review by jurisdiction
- security testing

## Deferred

Employment, housing, credit or insurance eligibility decisions remain deferred
until the applicable regulatory/compliance obligations have been designed and
reviewed.
