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
provider adapters + public-source research
   ↓
evidence graph
   ↓
entity / account correlation
   ↓
AI-assisted gap analysis
   ↓
human-readable report with confidence and sources
```

The dashboard will eventually accept multiple identifiers and files in one
case. AI can help extract candidate identifiers, find contradictions and
suggest the next research step, but it cannot create evidence.

## Current status

**M0 — public foundation is complete.**

The repository now has:

- a public Apache-2.0 project with explicit third-party/source boundaries;
- product, architecture, roadmap and continuity documents;
- a governed FastAPI intake API with purpose and consent checks;
- a responsive Next.js case-intake dashboard shell;
- provider/contact-risk planning without live provider execution;
- GitHub CI for the API on Python 3.11 and 3.13;
- GitHub CI for web lint, TypeScript checking and production build.

The next milestone is **M1 — evidence core**. Live OSINT provider calls,
username/social discovery, document-content ingestion, AI inference, persistent
case storage, production authentication and report export are not implemented
yet.

## Intended modes

- self-audit
- consented due diligence
- public-source research
- professional credential verification

Regulated eligibility decisions such as employment, housing, credit and
insurance are blocked in the bootstrap. Supporting those uses later would
require a separate legal/compliance workstream rather than a UI toggle.

## Repository map

```text
apps/web/                  Next.js dashboard
services/api/              FastAPI API + policy/evidence core
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
