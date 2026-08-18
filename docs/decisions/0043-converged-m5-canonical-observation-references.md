# ADR 0043 — Converged M5 evaluations reference canonical observations

Status: accepted for V2-D privacy closure

## Context

A retained converged report already stores each provider observation under its research node. The live M5 projection also copied the candidate source name and source locator into every evaluation record. That second copy was not a separate evidence authority; it repeated provenance that the node observation already owned.

Retaining duplicate locators increases personal-data surface and makes later redaction or schema changes easier to drift. M5 still needs an unambiguous way to identify which canonical observation was evaluated.

## Decision

Each live M5 candidate records its zero-based observation index within the owning research node. Retained M5 evaluations now expose:

- `candidate_node` — the canonical research-node key;
- `candidate_observation_index` — the index into that node's `observations` array.

They no longer copy `candidate_source` or `candidate_source_locator`.

The ephemeral M1-M5 graph may still use the full source and locator while evaluating evidence. This decision changes only retained report ownership; it does not change provider execution or correlation semantics.

The private operator UI resolves new evaluations through the canonical node observation. It keeps read-only support for the legacy source/source-locator fields so already-retained cases remain readable until they expire or are deleted; new backend reports do not emit those duplicate fields.

## Consequences

Positive:

- complete provider provenance has one retained owner in the canonical node observation;
- M5 retains a deterministic reference without copying the locator;
- an arbitrary provider detail and a candidate locator can be regression-tested as single-copy retained values;
- deletion/redaction ownership is clearer;
- old retained cases remain usable without rewriting historical JSON.

Costs:

- consumers that want the candidate source or locator must resolve `candidate_node` plus `candidate_observation_index` against the canonical node observation;
- observation order within a retained node is therefore part of the report reference contract;
- the UI temporarily understands both the new reference form and the older retained representation.

## Boundaries

This does not remove provenance from lead decisions or graph edges where those records must explain non-executed or cross-node traversal origins. It does not change M5 factor weights, calibration status, identity-claim semantics, recursion limits, provider coverage, credentials, or the zero-spend baseline.
