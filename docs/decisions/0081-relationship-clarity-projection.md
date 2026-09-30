# ADR 0081 — Fail-closed relationship clarity projection

## Problem

The retained converged report contains canonical observations, source-run state and deterministic M5 factors, but older M5 factor payloads do not retain the observation and identifier references used by the ephemeral correlation graph. A relationship visualization cannot safely reconstruct those references from similar usernames, co-occurring provider results or source execution outcomes.

## Decision

`relationship-clarity-projection-v1` is an authenticated, read-only projection derived on demand from one retained case. It is not stored as a second graph and contains no score, percentage, probability or identity claim.

New M5 factor payloads retain canonical `observation_refs` and `identifier_refs`. These references point back to existing converged-report nodes and observations; ephemeral evidence-store UUIDs are never exposed. The projection resolves every active factor reference and its source-run record before returning a relationship.

Relationships have exactly three semantic states:

- `corroborated` for an applied exact confirmed-identifier overlap or independent cross-link;
- `unresolved` for other applied evidence that still requires human judgment;
- `contradiction` only for an applied explicit hard-contradiction veto.

Provider failure, no match, unavailable, blocked, unattempted, budget-stopped and unknown coverage states never create nodes or edges. Relationship provenance must resolve to a canonical observation whose retained source-run state is `executed` with a `results_returned` reason. Suppressed, stale and not-applicable factors are omitted.

The private endpoint is `GET /v1/cases/{case_id}/relationship-clarity`. It requires the existing admin session and returns `Cache-Control: no-store`. A historical or malformed case without complete canonical factor references returns a fail-closed `409`; the service does not hydrate or infer missing relationships.

## Consequences

New converged cases are graphable without changing M5 scoring semantics or persisting another copy of retained evidence. Existing cases remain readable through the normal case endpoint, but relationship clarity is unavailable when their retained factor references are incomplete.

The projection contains typed identifier and observation nodes plus factor-backed edges. It remains deterministic and non-probabilistic, and it exposes timestamps only where actually retained: case creation and M5 evaluation context. Observation timestamps remain absent rather than invented.

## Out of scope

This decision does not add a graph renderer, infer identity, change factor weights, migrate historical cases, reinterpret source outcomes, add analytics or alter deletion and retention behavior.
