# ADR 0058 — M10 comparisons carry deterministic replay fingerprints

Status: accepted

## Context

M10 already runs labelled fixtures through the production frontier and records count-only graph and operational outcomes. Those counters are deterministic, but there was no compact way to prove which exact fixture truth and frontier policies produced a saved comparison. A later edit to a label, source fixture, lead ordering or limit could therefore reproduce similar-looking counters without being the same experiment.

## Decision

Add a versioned replay record for M10 cohort comparisons.

The record contains two SHA-256 digests:

- `input_digest` covers the labelled fixture definitions and the baseline/candidate frontier policies;
- `result_digest` covers the deterministic comparison output produced from those inputs.

Top-level fixture and candidate-scenario ordering is canonicalized because it is not semantically meaningful to cohort aggregation. Lead ordering under a fixture parent is preserved because it can affect frontier admission and is therefore part of the experiment definition.

The digest payload is canonical JSON with an explicit schema version. The record returns the existing comparison object unchanged; it does not create a new runtime scheduler or persistence path.

## Boundaries

Replay fingerprints are experiment identity, not evidence quality, reliability, confidence or identity probability. A matching digest proves that the same canonicalized experiment definition produced the same deterministic comparison payload; it does not prove that the fixtures represent the wider population.

No production recursion limit changes. No provider call, credential, paid dependency or new retained case data is introduced.

## Consequences

M10 can now attach a compact, reproducible identity to a controlled comparison before adding factor ablations or larger labelled cohorts. A changed label or frontier policy necessarily changes the input digest; a changed evaluation result necessarily changes the result digest.

The next evaluation work can use these fingerprints as the replay anchor for controlled factor ablations and defensibly labelled cohort expansion.