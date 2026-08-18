# ADR 0044 — Converged provenance uses canonical observation references

Status: accepted for V2-D privacy closure

## Context

A retained converged report previously copied the same admitted-pivot source and locator into the parent node observation, the corresponding `lead_graph.decisions` entry, and the graph edge. The extra copies did not provide independent evidence. They only increased retained personal-data surface and created multiple provenance fields that could drift.

Issue #76 initially proposed making the edge reference the admitted lead decision while leaving the decision's source and locator in place. That would still retain the same locator twice because the canonical parent observation already owns the provider provenance. The stronger single-owner model is therefore required.

## Decision

For new retained converged reports:

- the canonical parent node observation is the only retained owner of provider `source` and `source_locator`;
- every lead decision stores `source_observation_index`, which points into its `parent_key` node's observation array;
- every admitted edge stores `lead_decision_index`, which points into `lead_graph.decisions`;
- edges retain only structural parent/child/reason data plus the decision reference;
- lead decisions retain lead kind/value, disposition, decision, source field and child key, but do not copy provider source/locator;
- the writer validates every observation and decision reference before returning a new report;
- a shared reader fails closed on missing, malformed, out-of-range or structurally inconsistent references.

In-memory traversal records still keep their full `LeadCandidate` provenance. This change is about retained-report ownership, not graph evaluation semantics.

## Private UI compatibility

The current admin UI reads `edges[*].source` and `source_locator`. Rewriting that UI in the same privacy change would unnecessarily widen the block. `CaseStore` therefore keeps the canonical de-duplicated JSON in SQLite and adds those two legacy edge fields only to the in-memory/API response by resolving the canonical observation reference. Cases retained before ADR 0044 already contain the legacy fields and remain readable unchanged.

The compatibility projection is not written back to SQLite.

## Consequences

Positive:

- one admitted-pivot provider locator has one retained owner;
- edge, decision and observation provenance cannot silently drift;
- duplicate, review-only, display-only, blocked and other non-executed lead origins remain independently represented through decision records that reference their actual source observation;
- old retained cases remain readable by the existing private UI;
- provider calls, recursion budgets, graph evaluation and M5 semantics do not change.

Costs:

- new retained reports have reference-bearing internal structure that must be validated before use;
- the temporary API compatibility projection duplicates edge provenance in transit, though not in retained storage;
- a future private-UI schema cleanup should consume the references directly and remove the compatibility projection.

## Boundaries

This decision activates no provider or API, introduces no credential or paid dependency, changes no retention duration, does not increase recursion limits and does not change identity/correlation semantics.
