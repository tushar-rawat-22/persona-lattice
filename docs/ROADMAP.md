# Roadmap

The roadmap is intentionally evidence-first. Social discovery comes after the
data model and policy gates, not before them.

## M0 — public foundation

- repository, license and source policy
- product architecture
- intake API
- dashboard shell
- CI
- continuity handover

## M1 — evidence core

- persistent case/identifier/observation/claim schemas
- deterministic normalization
- provenance and freshness model
- redaction utilities
- synthetic fixtures only

## M2 — file intake + AI extraction

- safe multi-file upload
- text extraction for supported documents
- AI-assisted identifier extraction
- human confirmation before external queries
- prompt-injection isolation for uploaded content

## M3 — provider framework

- adapter protocol
- retry/rate-limit controls
- source-policy metadata
- phone-provider adapters for development
- public web-search adapter
- no provider secrets in browser or Git

## M4 — username and public-account discovery

- Maigret adapter
- Sherlock adapter
- independent account verification
- license-review gate for additional datasets/tools

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
