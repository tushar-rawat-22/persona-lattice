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
- evidence/correlation model grows in the API first
- provider adapters are isolated behind a protocol
- public docs live under `docs`
- `THIRD_PARTY.md` tracks license/integration boundaries

## Current milestone

**M0 — public foundation: COMPLETE.**

Implemented and published:

- repository, Apache-2.0 license and source policy;
- architecture/product/roadmap documentation;
- governed case-intake API;
- phone/email/username intake normalization;
- consent and purpose enforcement;
- provider/contact-risk planning with no live provider execution;
- Next.js case-intake dashboard shell;
- CI for API on Python 3.11 and 3.13;
- CI for web lint, typecheck and production build.

### M0 verification

- governed API commit: `2dd8d12ab96819b182a9bf563d1a9d946b0b366c`
- backend warning-cleanup commit: `6fb1d305b4d198cff8a35d3a1f9daffc93a95e47`
- dashboard/CI implementation commit on `main`: `8cc62091865d71ff1177877c4e5337a463436628`
- dashboard/CI PR: `#2`, merged after its CI run passed
- post-merge `main` CI run: `31901840132`, conclusion `success`
- API matrix: Python 3.11 PASS, Python 3.13 PASS
- web: install PASS, lint PASS, typecheck PASS, production build PASS

No live OSINT provider calls, real subject data, AI inference, persistent case
storage, production authentication or report export were introduced in M0.

## Next work

**M1 — evidence core.**

Build and test the data model before any live provider integration:

- persistent `Subject`, `Identifier`, `Observation`, `Claim` and `EvidenceLink` models;
- deterministic normalization separate from transport/API code;
- provenance and freshness rules;
- redaction utilities;
- synthetic fixtures only;
- invariants that prevent AI output from being stored as source observations.

Do not start live provider adapters until these invariants are covered by tests.

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
