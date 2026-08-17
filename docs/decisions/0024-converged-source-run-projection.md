# ADR 0024 — Converged nodes expose source-run state

Status: accepted for V2-D architecture closure

## Context

PersonaLattice already has a typed source-run contract, explicit execution-outcome mapping and a deterministic privacy-bounded report projection. Converged reports still exposed observations and warning strings only, so the operator-facing node contract had no stable place for source lifecycle state.

The execution boundary is being migrated incrementally. Existing custom/test runners and older quick-research paths do not yet populate typed source-run records, so report integration must not fabricate states from observations or warning text.

## Decision

Add a `source_runs` projection to every converged node payload using the existing `build_source_run_report()` serializer.

When a quick-research report exposes typed `source_runs`, the node serializes them deterministically. When a legacy/custom runner does not expose that attribute, the node emits an explicit empty source-run projection.

The projection remains privacy-bounded: it contains logical source name, lead kind, state/reason, observation count and execution/terminal flags only. Identifier values, source locators, provider payloads, credentials and exception text remain outside this structure.

## Consequences

This creates the stable retained-report location needed by the next integration block without changing the report version or breaking custom research runners. It also prevents a tempting but incorrect shortcut: inferring `not_found`, `unavailable` or `budget_stopped` from warning strings or the absence of observations.

The projection is intentionally empty until the corresponding quick-research path supplies factual source-run records. That incompleteness is visible rather than guessed away.

## Next step

Populate typed source-run records at the real quick-research execution boundary, beginning with governed provider calls and local deterministic sources. Preserve the distinction between local pre-call budget stops, optional-unconfigured sources, attempted remote failures and completed zero-result calls.

No provider, credential, paid dependency, recursion limit or M5 identity semantic changes in this decision.
