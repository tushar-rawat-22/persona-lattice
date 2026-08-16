# ADR 0008 — local evidence dashboard before production case access

## Status

Accepted for M6 implementation.

## Context

M5 can persist explainable correlation runs over stored evidence. The next product
need is an operator view that makes source provenance, stale evidence, factual
claims, candidate accounts and M5 factors understandable without collapsing them
into one misleading "identity confidence" number.

The original roadmap placed dashboard work before production authentication and
authorization. A dashboard that directly exposes stored personal cases through
an unauthenticated case-by-ID endpoint would create the wrong security boundary:
the richest read surface would exist before object-level access control,
retention/deletion, audit and abuse controls.

M6 therefore needs useful presentation work without accidentally turning local
research state into a production personal-data API.

## Decision

M6 uses a bounded, read-only single-case contract and remains local/development
and synthetic-fixture driven.

1. `app.dashboard` may read existing M1 evidence and M5 correlation records but
   does not write evidence, run providers or invoke the correlation engine.
2. M6 does not register a stored-case HTTP read/list endpoint. Production case
   endpoints are deferred to M7, where authentication and object-level
   authorization can be designed with them rather than bolted on later.
3. The read model exposes normalized identifiers, explicit provenance,
   freshness, bounded summaries, evidence links and account-candidate state. It
   does not serialize arbitrary `Observation.payload` dictionaries.
4. Source Observations, factual Claims and derived correlation triage remain
   separate typed objects in the contract.
5. Stored M5 canonical output is validated before presentation: its SHA-256
   output digest, subject, candidate, policy version and evaluation time must
   agree with the persisted run.
6. M5 output must remain `calibration_status=uncalibrated` and
   `is_identity_claim=false`; drift is a read-model error rather than something
   the dashboard silently reinterprets.
7. Correlation factors may reference only observations and identifiers present
   in the same case read model.
8. Account candidates must explicitly remain non-identity evidence and retain a
   visible source identifier.
9. Read-model field sizes and collection counts are bounded so presentation does
   not become an unbounded serialization path.
10. M6 fixtures contain synthetic identities only. Raw case data, screenshots,
    credentials and real-person exports do not enter Git.
11. The UI must label M5 output as an uncalibrated evidence-strength triage
    score, never a probability or calibrated confidence percentage.
12. Hard contradictions/vetoes and stale evidence are first-class visible
    states, not hidden behind secondary detail views.
13. M6 adds no AI/ML/embedding/biometric identity decision and does not trigger
    autonomous provider expansion.

## Why not add a development-only case endpoint?

Environment checks and feature flags do not provide object-level authorization.
A route that accepts a stored subject identifier is the same architectural shape
that production will eventually need to protect. Creating it now would either
encourage accidental exposure or force M7 to replace an already-consumed
contract.

Keeping the M6 boundary as an in-process service plus synthetic presentation
fixture lets us validate the product and read-model semantics without creating a
network-accessible personal-data surface.

## Consequences

- M6 can build and test the dashboard while production case access remains
  impossible by construction.
- The browser cannot enumerate or request stored subjects during M6.
- Arbitrary provider payload fields cannot leak merely because they exist in the
  evidence database.
- The contract gives M7 a reviewed presentation model to authorize later instead
  of forcing authentication work to invent data semantics at the same time.
- Local integration is less convenient than a temporary case API, but the
  inconvenience is deliberate and removes a class of avoidable security debt.
- When M7 introduces production case reads, this ADR must be revisited together
  with authentication, per-object authorization, retention/deletion, audit and
  abuse controls.
