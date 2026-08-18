# PersonaLattice

PersonaLattice is a private-admin, evidence-first public-source research system.
It takes a phone number, email address, username/handle, public URL or uploaded
document/image and builds an attributable research record without pretending
that incomplete public data is certain identity.

The public web surface is intentionally safe to expose: unauthenticated visitors
can see the product shell/demo, but real case data is returned only after the
single configured admin session is authenticated server-side.

PersonaLattice is deliberately **not** a "type a number and magically know
everything" product. Sources can be missing, stale, duplicated or wrong. A field
that cannot be established remains unknown rather than being invented.

## Private V1 workflow

```text
admin login
   ↓
phone / email / username / public URL / file intake
   ↓
normalization + purpose/source policy
   ↓
approved public-source research
   ↓
bounded public identifier convergence
   ↓
canonical evidence graph
   ↓
deterministic M5 evidence-strength triage
   ↓
private retained case with provenance, gaps and contradictions
```

## Current capabilities

The private V1 implementation includes:

- a single-admin Argon2-backed login boundary with opaque HttpOnly session
  cookies, expiry/logout, CSRF protection and login throttling;
- a public-safe Next.js shell that does not receive real case payloads before
  authentication;
- phone normalization and numbering-plan metadata without claiming subscriber
  identity;
- governed username discovery over a fixed reviewed Sherlock site subset;
- GitHub, GitLab and Codeforces public-profile enrichment;
- exact GitLab public-email matching where the email is explicitly exposed by
  that public profile;
- optional exact-match discovery through a licensed Brave public web index when
  `BRAVE_SEARCH_API_KEY` is configured;
- canonical public URL metadata plus globally reachable DNS infrastructure
  addresses, explicitly labelled as site/domain infrastructure rather than a
  person's device IP or physical location;
- bounded two-hop/twelve-node convergence over attributable public email,
  username and website fields;
- source/provenance edges for every automatic research pivot;
- duplicate-pivot suppression and local provider rate/resource budgets;
- PDF, UTF-8 text, JPEG and PNG metadata/intake under bounded extraction rules;
- deterministic M5 evaluation of live public account candidates using the same
  semantics as the research core;
- M5 results that remain `calibration_status=uncalibrated` and
  `is_identity_claim=false`, with the score displayed as evidence-strength
  triage and never as identity probability;
- private SQLite case retention with a 30-day default, expiry purge, per-case
  deletion and delete-all;
- a privacy-minimized audit ledger that records operations without copying
  research seeds, provider payloads or session secrets;
- GitHub CI on Python 3.11 and 3.13 plus Ruff, `npm ci`, lint, strict TypeScript
  and production Next.js build;
- a zero-spend local operating path that requires no paid hosting or database;
- an optional paid Render reference topology kept outside the repository root.

## Evidence and safety rules

- AI is not evidence.
- Source observations, factual claims and correlation decisions are separate.
- Same-handle reuse is weak evidence, not proof of identity.
- A discovered public identifier is a research pivot, not an identity claim.
- Stale evidence and contradictions remain visible.
- A hard contradiction can veto positive evidence.
- Real case data and provider credentials never enter Git.
- No private-account bypass, credential/OTP theft, account-recovery probing,
  CAPTCHA/WAF evasion or unauthorized system access.
- No covert IP/device discovery, tracking-link collection or deanonymization.
- No Internet-scale biometric/face identification.
- Regulated employment, housing, credit and insurance eligibility decisions are
  outside the product boundary.

## Zero-spend baseline

PersonaLattice's default operating path is local and does not require paid APIs,
hosting, databases, proxies or enrichment. See `docs/ZERO_SPEND_RUNBOOK.md` for
the exact setup.

Broad exact-match public web discovery through Brave is optional. Set
`BRAVE_SEARCH_API_KEY` server-side only if that metered integration is
deliberately enabled. Without it, PersonaLattice continues to run its other
local and public-source research paths.

The old paid Render topology is retained only as an explicit reference at
`deploy/render-paid.yaml`. It is not the default deployment contract and is not
required for the product to function.

## Repository map

```text
apps/web/                         public shell + private admin console
services/api/                     FastAPI authentication/research/case API
services/api/app/evidence/        canonical evidence models and normalization
services/api/app/correlation/     deterministic M5 evidence-strength engine
services/api/app/convergence.py   bounded public-evidence pivot graph
services/api/app/live_m5.py       live evidence admission into M5 semantics
services/api/app/public_search.py optional licensed public-index discovery
docs/                             architecture, runbooks, roadmap and decisions
deploy/render-paid.yaml           optional paid Render reference topology
THIRD_PARTY.md                    license/integration boundary
SECURITY.md                       sensitive-data handling rules
```

## Local development

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

For the private one-admin workflow, follow `docs/ZERO_SPEND_RUNBOOK.md`; it covers
the local admin hash, cookie mode and data paths without putting secrets in Git.

## Optional deployment secrets

Hosted or optional integrations may require server-side configuration such as:

- `PERSONALATTICE_ADMIN_USERNAME`
- `PERSONALATTICE_ADMIN_PASSWORD_HASH`
- `BRAVE_SEARCH_API_KEY` (optional and not part of the zero-spend baseline)

The password itself is never stored in Git; the API expects an Argon2 password
hash.

## License

Original PersonaLattice code is Apache-2.0. Third-party licenses and external
source terms remain separate integration boundaries. See `THIRD_PARTY.md`.
