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

**Status: next — Issue #7**

- versioned adapter/request/result/error contracts
- central purpose/consent/source-policy enforcement before execution
- source/license/contact-risk metadata
- retry classification, rate budgets, concurrency and timeout controls
- server-side secret boundary and public-safe structured logs
- synthetic provider first, with provenance-bearing observations
- narrowly scoped development provider only after exact terms/privacy review

The earlier idea of jumping directly to live phone and web adapters is
intentionally tightened: framework and policy behavior must first pass with
synthetic providers. Public web access must not become an arbitrary URL fetcher.

## M4 — username and public-account discovery

- Maigret adapter
- Sherlock adapter
- independent account verification
- license-review gate for additional datasets/tools
- reuse the M3 execution and policy boundary rather than bypassing it

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
