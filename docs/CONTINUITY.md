# Continuity

This is the public-safe handover for continuing PersonaLattice in a new ChatGPT
conversation without rebuilding context from scratch.

## How to use this file

At the start of a new project chat:

1. ask ChatGPT to read this file and the linked status/architecture documents;
2. verify the repository state rather than trusting this file blindly;
3. continue from the "Next work" section;
4. update this file after every meaningful milestone.

Do not put API keys, real investigation identifiers, private case data or
unredacted screenshots in this file.

## Project

- Name: PersonaLattice
- Repository: `tushar-rawat-22/persona-lattice`
- Visibility: public
- Local checkout: `~/persona-lattice`
- License: Apache-2.0 for original code
- Product: evidence-first identity intelligence and consented/public-source research

## Non-negotiable design rules

- AI is not evidence.
- Every factual claim must trace to source observations.
- Raw personal-data case files never enter Git.
- Provider credentials never enter Git.
- Source/license/purpose gates exist before provider execution.
- Silent/public mode excludes sources with subject-contact risk.
- Regulated employment/housing/credit/insurance decisions are blocked in the bootstrap.

## Architecture baseline

- Next.js web dashboard under `apps/web`
- FastAPI service under `services/api`
- SQLAlchemy evidence core under `services/api/app/evidence`
- provider adapters are isolated behind a protocol
- public docs live under `docs`
- `THIRD_PARTY.md` tracks license/integration boundaries

## Completed milestones

### M0 — public foundation: COMPLETE

Published:

- repository, Apache-2.0 license and source policy;
- architecture/product/roadmap documentation;
- governed case-intake API;
- consent and purpose enforcement;
- provider/contact-risk planning with no live provider execution;
- Next.js case-intake dashboard shell;
- CI for API on Python 3.11 and 3.13;
- CI for web lint, typecheck and production build.

Key M0 verification:

- governed API commit: `2dd8d12ab96819b182a9bf563d1a9d946b0b366c`
- backend warning-cleanup commit: `6fb1d305b4d198cff8a35d3a1f9daffc93a95e47`
- dashboard/CI implementation commit: `8cc62091865d71ff1177877c4e5337a463436628`
- post-merge M0 CI run: `31901840132`, conclusion `success`

### M1 — evidence core: COMPLETE

Published through PR `#4`:

- persistent `Subject`, `Identifier`, `Observation`, `Claim` and `EvidenceLink`
  SQLAlchemy models;
- database-agnostic UUIDs and SQLite development/test persistence;
- explicit SQLite foreign-key enforcement;
- deterministic phone, email, username, URL, name and organization
  normalization outside the HTTP layer;
- source provenance, retrieval timestamps and optional expiry/freshness;
- support/contradict/unresolved evidence relationships;
- AI may originate a `Claim` but `ai` is not an allowed observation source;
- public-safe phone/email redaction helpers;
- ADR `0003-evidence-core-persistence.md`;
- synthetic-only tests; no live subject or provider data.

M1 verification:

- initial evidence commit: `ac241696792553ea767677606efefc4275be5a8d`
- conservative-normalization correction: `21651e2c1ce56d57a08e569af6652ca912096778`
- final test-alignment commit: `35a6be3ba3609b1324158c62f02240b38db91f26`
- merge commit on `main`: `22d8b4c100db4861ad1890bcb224f890cd652210`
- final PR CI run: `31902885290`, API 3.11 PASS, API 3.13 PASS, web PASS
- post-merge `main` CI run: `31902946010`, API 3.11 PASS, API 3.13 PASS, web PASS

During review we rejected generic case-folding for email local-parts and
usernames, and rejected stripping URL fragments. Those equivalence rules can be
platform-specific, so the core now preserves them and leaves provider-specific
canonicalization to later adapters. One intermediate PR run failed because an
older deduplication test still expected the discarded behavior; the test was
corrected and the final PR/main runs are green.

No live OSINT provider calls, real subject data, provider credentials, AI
execution, production authentication or report export have been introduced.

## Next work

**M2 — safe file intake and AI-assisted extraction.**

Before any model sees uploaded content:

- enforce file-count and byte-size ceilings;
- use an allowlist of supported document types;
- keep uploads outside Git and outside public logs;
- treat filenames and document content as untrusted input;
- extract text in a bounded worker boundary;
- store extraction results as source observations with provenance;
- isolate uploaded instructions from system/developer instructions;
- require human confirmation of extracted identifiers/claims before they can
  trigger external research;
- keep live AI/provider execution disabled until these controls are covered by
  synthetic tests.

## Bootstrap recovery record

The initial M0 bootstrap was interrupted twice before any backend code was
published:

1. macOS resolved `python3` to Python 3.9.6 while the API requires Python 3.11+;
2. after moving the local environment to Python 3.13, the broad Ruff dependency
   range installed Ruff 0.16, whose expanded default rule set changed the lint
   contract and raised import-format diagnostics.

Recovery decision:

- keep Python >=3.11;
- use Homebrew Python 3.13 locally;
- pin Ruff 0.15.15 for the bootstrap instead of relying on moving defaults;
- define the bootstrap lint rule set explicitly;
- publish backend code only after lint, compile, tests and an API smoke test pass.

## Backend warning cleanup

After the governed intake API was published, local verification exposed two
upstream deprecations rather than functional failures:

- Starlette's TestClient now prefers `httpx2` over `httpx`;
- the old 422 status constant was renamed to `HTTP_422_UNPROCESSABLE_CONTENT`.

The baseline now uses HTTPX2 2.9.0 for TestClient, the current 422 constant,
and treats Starlette deprecation warnings as test failures.

## Update discipline

For every milestone update:

- current repository/branch;
- latest meaningful commits;
- tests and verification run;
- what changed;
- what did not change;
- unresolved risks;
- next authorized work.

The point is continuity, not marketing copy.
