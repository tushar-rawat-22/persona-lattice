# ADR 0021 — Source execution state is an explicit report contract

Status: accepted for V2-D architecture completion

## Context

PersonaLattice already distinguishes lead disposition and frontier outcomes, but source execution itself is still mostly inferred from observations and warnings. That is too ambiguous for a recursive research product. An operator needs to know whether a source actually ran, returned no match, was never configured, was blocked before execution, hit a local budget, or failed during execution.

The distinction matters for evidence quality, cost control and debugging. In particular, `not_found` must never be confused with `unavailable`, and an optional metered provider that is not configured must not look like a failed query.

## Decision

Add a typed source-run contract under `app.intelligence.source_states`.

The stable states are:

- `executed` — the source returned one or more admitted observations;
- `not_found` — execution completed and returned no matching observation;
- `queued` — eligible work exists but has not run yet;
- `review_required` — policy requires operator review before execution;
- `display_only` — the clue is context and is intentionally non-executable;
- `blocked` — policy forbids execution;
- `unavailable` — execution could not produce an answer because the optional source is not configured, the provider failed, or the remote service rate-limited the request;
- `budget_stopped` — a local PersonaLattice budget prevented execution from starting.

Each state has a constrained reason vocabulary. Invalid state/reason combinations fail closed.

A source-run record stores the source name, lead kind, state, reason, observation count and source locators. It deliberately does not copy the lead value into another report structure. Existing lead/evidence records remain the authority for identifiers and provenance.

## Execution semantics

The contract exposes whether a source execution attempt is actually proven by the outcome:

- `executed` and `not_found` prove an attempt;
- provider failure and remote rate-limit outcomes prove an attempt;
- optional-not-configured, local-budget, policy and queue states do not.

The property is deliberately named `execution_attempted`, not `network_attempted`. Local deterministic sources such as normalization can execute without network I/O, and the report contract must not invent transport claims it cannot prove.

Only `executed` may retain observation counts or source locators. This prevents a blocked, unavailable or not-found state from smuggling positive-looking evidence into the report.

## Consequences

This block defines the contract only. Existing quick-research and retained-case report payloads are not rewritten in the same change. The next integration block can map ProviderRuntime/frontier outcomes into these records without inventing another state vocabulary.

The contract is additive and does not change source coverage, provider execution, recursion limits, M5 correlation, credentials or cost behavior.

## Next review

Wire the typed source-run records into the retained convergence/report path and deterministic synthetic fixtures. After that, migrate the final legacy optional Brave execution path behind ProviderRuntime without making it part of the zero-spend baseline.
