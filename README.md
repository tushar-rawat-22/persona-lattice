# PersonaLattice

PersonaLattice is a private, evidence-first public-source research workbench. It accepts known clues such as a phone number, email address, username, public URL or uploaded document/image and builds an attributable research record around them.

It is deliberately conservative about identity. Public records can be missing, stale, duplicated or wrong, so the system keeps observations, correlations and provenance separate. Unknowns stay unknown instead of being filled in by a model.

The repository is public. Real research data is not. Unauthenticated visitors only receive the synthetic/demo surface; real intake, provider execution and retained cases sit behind the server-side admin session and CSRF boundary.

## Project status

The one-admin application has passed its first production-shaped host and browser acceptance gate (`LAUNCH_CANDIDATE_1`). It is usable as a project/private operator tool today.

The canonical public observer is a static, synthetic/read-only Cloudflare Pages deployment that is independent of the founder Mac. The authenticated private beta is validation infrastructure: it can be offline when its host sleeps and is not advertised as an always-on public service. The next private-beta reliability step is a provider-neutral zero-cash Linux deployment path with persistent protected storage, exact-release identity and bounded ingress; see `docs/LIVE_BETA.md` and `docs/DEPLOYMENT.md`.

Post-LC1 product work continues without holding the usable build offline. The current focus is operator efficiency and decision clarity rather than cosmetic dashboard work.

## How a case works

```text
admin login
   ↓
known clues / public URLs / reviewed files
   ↓
normalization + purpose/source policy
   ↓
approved bounded public-source research
   ↓
attributable evidence + typed source states
   ↓
bounded public-identifier convergence
   ↓
deterministic M5 evidence-strength triage
   ↓
retained private case with provenance, gaps and contradictions
```

The operator workspace is built around the questions that matter during an investigation: what is corroborated, what conflicts, what remains unknown, which sources ran or failed, why a correlation exists and where an observation came from.

## Current capabilities

The private V1 includes:

- one-admin Argon2id authentication with opaque HttpOnly sessions, expiry/logout, CSRF checks and login throttling;
- a same-origin Next.js/FastAPI application boundary so the browser does not need the private API origin;
- bounded phone numbering-plan metadata without subscriber-identity claims;
- reviewed username discovery plus exact/bounded public-source integrations;
- exact public profile/entity/repository/record paths across admitted sources including GitHub, GitLab, Keybase, Bluesky, Stack Overflow, OpenAlex, Wikidata, Zenodo, ROR, Companies House, DBLP, GLEIF and SEC EDGAR where their exact applicability/configuration requirements are met;
- exact DOI metadata through Crossref with bounded DataCite fallback;
- public RDAP domain metadata and DNS infrastructure metadata without treating infrastructure IP addresses as a person's device/location;
- Wayback capture-availability metadata without archived-page harvesting;
- bounded public-identifier convergence with duplicate-pivot suppression and process-owned provider budgets;
- PDF, UTF-8 text, JPEG and PNG intake under bounded extraction/review rules;
- deterministic M5 evidence-strength triage that remains uncalibrated, non-probabilistic and `identity_claim=false`;
- an operator decision surface for corroboration, conflicts, open questions, source execution state and provenance;
- searchable/filterable retained-case navigation, explicit loading/failure/session states and guarded deletion;
- SQLite case retention with expiry/purge, case deletion and verified backup/restore tooling;
- a privacy-minimized audit ledger that avoids copying research seeds, provider payloads or session secrets;
- CI across Python 3.11/3.13, Ruff, dependency checks, web lint/typecheck/contracts/build, production API image and launch-process smoke.

Some providers require optional server-side configuration. Missing optional configuration fails closed; it does not make the application invent enrichment.

## Boundaries

PersonaLattice does not provide private-account bypass, credential/OTP collection, account-recovery probing, CAPTCHA/WAF evasion, covert personal/device IP discovery, live tracking, hidden KYC/government-ID acquisition, broad ownership traversal, contact harvesting, Internet-scale biometric identification or regulated employment/housing/credit/insurance eligibility decisions.

A same-handle match is weak evidence, not proof. A discovered public identifier is a research lead, not an identity claim. A hard contradiction remains visible even when other evidence agrees.

## Running locally

Backend requires Python 3.11 or newer.

```bash
python3 -m venv .venv
.venv/bin/pip install -e "./services/api[dev]"
.venv/bin/pytest services/api/tests
.venv/bin/uvicorn app.main:app --app-dir services/api --reload --host 127.0.0.1 --port 8000
```

Frontend:

```bash
cd apps/web
npm ci
npm run dev
```

Open `http://127.0.0.1:3000`.

For the authenticated one-admin setup, use `docs/ZERO_SPEND_RUNBOOK.md`. Keep passwords, hashes, provider credentials, retained databases and real evidence outside Git.

## Deployment

PersonaLattice's required baseline remains usable without paid enrichment APIs or a hosted database. The canonical public observer is static and synthetic/read-only; it does not depend on the private operator host.

For the stateful private beta, the current zero-cash path is documented in `docs/LIVE_BETA.md` and `docs/DEPLOYMENT.md`: prepare the provider-neutral Linux bundle first, keep SQLite on persistent protected storage, bind the API to loopback, and use bounded ingress such as Cloudflare Tunnel/Access when a suitable zero-cash host is available. Provider signup/capacity is treated as an external constraint, not a reason to weaken persistence or security.

Paid hosted references may remain in the repository as future fallback/migration evidence, but they are not a current founder action while the zero-cash constraint applies. A random Quick Tunnel is a short-lived validation/smoke tool, not an always-on private-beta endpoint. An ephemeral hosted filesystem is not acceptable for the current SQLite retained-case store.

## Documentation

Human-facing project documentation:

- `docs/PRODUCT_CHARTER.md` — what the product is and is not;
- `docs/ARCHITECTURE.md` — system structure and trust boundaries;
- `docs/DEPLOYMENT.md` — runtime and deployment requirements;
- `docs/LIVE_BETA.md` — current go-live choices and release gate;
- `SECURITY.md` — sensitive-data and security rules;
- `THIRD_PARTY.md` — third-party source/license boundary.

For a future maintainer or AI engineering session, start with `docs/CONTINUITY.md`. It is intentionally separate from the public product prose and records the current architecture, launch state, invariants, source-governance rules and resume procedure.

`docs/DOCUMENTATION_STANDARD.md` defines how those two audiences stay separate.

## Repository map

```text
apps/web/                         public shell + private operator workspace
services/api/                     FastAPI auth/research/case API
services/api/app/evidence/        canonical evidence models and normalization
services/api/app/correlation/     deterministic M5 evidence-strength engine
services/api/app/convergence.py   bounded public-evidence pivot graph
docs/                             architecture, operating docs and continuity
deploy/render-paid.yaml           optional paid hosted reference
THIRD_PARTY.md                    external integration/license boundary
SECURITY.md                       sensitive-data handling rules
```

## License

Original PersonaLattice code is Apache-2.0. Third-party licenses, provider terms and external-source data rights remain separate integration boundaries. See `THIRD_PARTY.md` and the source-admission records before changing provider scope.