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

## Bootstrap architecture

- Next.js web dashboard under `apps/web`
- FastAPI service under `services/api`
- evidence/correlation model grows in the API first
- provider adapters are isolated behind a protocol
- public docs live under `docs`
- `THIRD_PARTY.md` tracks license/integration boundaries

## Current milestone

M0 — public foundation.

Expected after bootstrap:

- repository exists publicly;
- policy/license docs committed;
- architecture/roadmap committed;
- intake API passes tests;
- dashboard builds;
- GitHub CI exists;
- initial roadmap issues exist.

## Next work

M1 — evidence core:

- persistent Subject / Identifier / Observation / Claim / EvidenceLink models;
- deterministic normalization;
- provenance/freshness rules;
- synthetic test fixtures;
- no live provider integration until these invariants are tested.

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
