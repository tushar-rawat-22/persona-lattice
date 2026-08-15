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

Mission 0 is a public architecture/bootstrap milestone.

Implemented in the bootstrap:

- public Apache-2.0 repository
- product and architecture documents
- source/license boundary
- continuity handover
- FastAPI intake/policy skeleton
- Next.js dashboard shell
- CI checks

Not implemented yet:

- live OSINT provider calls
- username/social discovery
- document content ingestion
- AI inference
- persistent case storage
- production authentication
- report export

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

Backend:

```bash
python3 -m venv .venv
.venv/bin/pip install -e "./services/api[dev]"
.venv/bin/pytest services/api/tests
.venv/bin/uvicorn app.main:app --app-dir services/api --reload --host 127.0.0.1 --port 8000
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
