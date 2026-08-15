# PersonaLattice

PersonaLattice is an evidence-first identity intelligence project. It is being
built to take a messy set of identifiers — names, phones, emails, usernames,
links, organizations and uploaded documents — and turn them into a
source-linked, confidence-scored research report.

The project is deliberately **not** a "type a phone number and magically know
everything" tool. Identity data is incomplete, duplicated and often wrong.
PersonaLattice treats every source as evidence that can support, contradict or
fail to resolve a claim.

## What we are building

The planned workflow is:

```text
case intake
   ↓
identifier extraction + normalization
   ↓
source policy / consent gate
   ↓
governed provider execution
   ↓
evidence graph
   ↓
entity / account correlation
   ↓
AI-assisted gap analysis
   ↓
human-readable report with confidence and sources
```

AI can help extract candidate identifiers, find contradictions and suggest the
next research step, but it cannot create evidence. Document text is treated as
untrusted source material, not as instructions to the application.

## Current status

**M0 through M3 are complete.**

The repository now has:

- a public Apache-2.0 project with explicit third-party/source boundaries;
- a governed FastAPI intake API with purpose and consent checks;
- a responsive Next.js case-intake dashboard;
- persistent SQLAlchemy evidence models for subjects, identifiers,
  observations, claims and evidence links;
- deterministic identifier normalization and public-safe redaction;
- provenance, retrieval time, expiry/freshness and evidence-relation semantics;
- bounded PDF and UTF-8 text upload validation and isolated extraction;
- review-only document-derived candidates that require explicit human
  confirmation before later research;
- a typed provider framework with centralized purpose, consent, contact-risk
  and candidate authorization;
- bounded provider retry, local rate budgets, concurrency, timeout and response
  size controls;
- server-side-only provider secret resolution;
- provenance-bearing provider observations that never become claims
  automatically;
- a synthetic provider used to verify the execution contract without network
  access;
- GitHub CI for the API on Python 3.11 and 3.13 plus web lint, TypeScript and
  production build checks.

The next milestone is **M4 — governed username and public-account discovery**
(Issue `#9`). Sherlock is the first planned existence-check adapter. Maigret is
a later enrichment candidate under a deliberately restricted mode. Same-handle
reuse is evidence, not identity proof.

No real external OSINT provider is executable yet. Live AI model calls,
production authentication, private-account access and report export are also
not implemented.

## Intended modes

- self-audit
- consented due diligence
- public-source research
- professional credential verification

Regulated eligibility decisions such as employment, housing, credit and
insurance are blocked. Supporting those uses later would require a separate
legal/compliance workstream rather than a UI toggle.

## Repository map

```text
apps/web/                  Next.js dashboard
services/api/              FastAPI API + policy/evidence/upload/provider core
docs/                      architecture, roadmap and decisions
docs/CONTINUITY.md         chat-to-chat project handover
THIRD_PARTY.md             license/integration boundary
SECURITY.md                handling rules for sensitive data
```

## Local development

Backend requires Python 3.11 or newer.

```bash
python3 --version
python3 -m venv .venv
.venv/bin/pip install -e "./services/api[dev]"
.venv/bin/pytest services/api/tests
.venv/bin/uvicorn app.main:app --app-dir services/api --reload --host 127.0.0.1 --port 8000
```

On macOS, if the system `python3` is older than 3.11:

```bash
brew install python@3.13
"$(brew --prefix python@3.13)/bin/python3.13" -m venv .venv
```

Frontend:

```bash
cd apps/web
npm install
npm run dev
```

Open `http://localhost:3000`.

## License

Original PersonaLattice code is Apache-2.0. Third-party licenses do not become
Apache-2.0 simply because an integration exists here. See `THIRD_PARTY.md`.
