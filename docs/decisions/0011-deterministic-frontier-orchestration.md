# ADR 0011 — Deterministic frontier orchestration

Status: accepted for V2 infrastructure

## Context

ADR 0010 introduced typed evidence leads and a fail-closed extractor. The first
foundation commit intentionally left private-V1 convergence running through its
existing sequential depth/node loop while the new frontier scheduler was tested
in isolation.

That separation was useful for landing the lead contract safely, but it cannot be
the long-term architecture. If the executor and the scheduler disagree about
which leads have been attempted or which budgets are exhausted, adding providers
or concurrency later could produce duplicate calls, unbounded fan-out, or report
states that cannot explain why a clue was not followed.

## Decision

The convergence engine now uses `LeadFrontier` as the run-local admission
authority for recursive public/authorized leads.

For every extracted lead the run records one explicit outcome:

- `admitted` — provider execution succeeded and produced a new graph node;
- `provider_failed` — execution failed and the reservation was released;
- `duplicate` — the lead or its normalized result was already known/attempted;
- `review_required` — the clue is visible but automatic research is not allowed;
- `display_only` — contextual evidence remains visible but is not executable;
- `depth_limit`, `node_limit`, `edge_limit`, `kind_limit`, or
  `parent_fanout_limit` — a deterministic budget stopped expansion.

`enqueue` is an internal transient reservation state and is not a final report
outcome.

## Reservation accounting

Budget is reserved before a provider call. Outstanding reservations count against
node, edge, lead-kind and parent-fanout ceilings.

This matters even though the current convergence runner is sequential: future
bounded concurrency must not be able to admit N simultaneous requests that each
individually saw the same last free slot.

A failed provider call releases its capacity, but the lead remains in the
attempted set for that run. The same clue is therefore not silently retried through
another provenance path while a different lead may still use the released budget.

## Backward-compatibility gate

Wiring in the frontier must not silently narrow private-V1 research coverage.
The convergence entry point therefore maps the existing `max_depth` and
`max_nodes` parameters into frontier limits while setting per-kind and per-parent
limits high enough to preserve the old behavior.

The stricter per-kind/fan-out defaults remain available as infrastructure but are
not activated for the production convergence path until labelled evaluation shows
that they improve reliability without hiding useful attributable evidence.

The retained report version remains `private-converged-evidence-report-v1` for
compatibility. V2 lead state is an additive `lead_graph` section with its own
policy version.

## Provenance of duplicate clues

Provider execution is deduplicated by canonical lead key, but provenance is not.
If two source observations independently emit the same email/username/URL, the
provider is queried once while both origins appear in `lead_graph.decisions`.

Traversal edges still represent admitted research expansion. The lead decision
records preserve additional origins that did not require another network call.
This avoids trading source provenance for request deduplication.

## Sensitive fields

Blocked sensitive values never become lead candidates, frontier reservations, or
lead decision payloads. The run may retain only the blocked field name so the
operator can see that policy rejected a class of data without copying the value
into the recursive graph.

## Consequences

Positive:

- one scheduler owns duplicate suppression and budgets;
- future concurrency has reservation-safe ceilings;
- the retained report explains why every reviewed clue was or was not followed;
- duplicate evidence origins remain inspectable without duplicate provider calls;
- private-V1 node/depth behavior remains compatible while the V2 policy is
  introduced additively.

Costs:

- reports become larger because non-executed lead decisions are explicit;
- provider failure and budget states become part of the report contract;
- future UI work must distinguish transient provider errors from negative
  evidence and policy stops.

Those costs are intentional. An intelligence graph should be able to explain its
frontier, not merely its successful nodes.
