# ADR 0057 — Count M10 source attempts and request-cost units before widening recursion

Status: accepted for M10 evaluation support

## Context

M10 already compares graph growth, duplicate suppression, provider failures, local budget stops and labelled pivot quality across deterministic frontier policies. The broader multi-kind cohort showed that depth 3 admitted extra wrong-labelled pivots, but the comparison still could not state how many additional source executions the wider frontier would permit.

Counting graph nodes alone is not enough. Duplicates, review-only clues and local frontier stops do not contact a source, while both successful provider executions and attempted provider failures do. Any operational comparison needs to preserve that distinction.

## Decision

Extend the M10 cohort counters with deterministic execution-cost units derived from the same `LeadFrontier` evaluation:

- `source_attempt_count` counts only leads that passed frontier admission and reached the simulated provider boundary;
- `successful_source_attempt_count` counts admitted pivots;
- `zero_yield_source_attempt_count` counts simulated provider failures;
- `observation_yield_unit_count` counts one synthetic yield unit for each successful fixture execution;
- `request_cost_unit_count` counts one abstract request-cost unit for each source attempt.

Duplicates, review-required/display-only/blocked clues and local frontier budget stops consume zero request-cost units because the provider boundary is never reached.

These are synthetic accounting units, not currency, billing estimates or provider reliability rates. The current fixture model represents one bounded request and one successful yield unit per admitted pivot. A future provider-specific fixture contract may add explicit multi-request or multi-observation weights if M10 needs that fidelity.

## Result on the current broadened cohort

Under depth 2 / 12 nodes, the six-fixture cohort produces 11 simulated source attempts: 9 successful yield-producing attempts and 2 zero-yield provider failures, for 11 request-cost units and 9 observation-yield units.

Under depth 3 / 12 nodes, the cohort produces 14 simulated source attempts: 12 successful yield-producing attempts and the same 2 zero-yield provider failures. The wider frontier therefore adds 3 request-cost units and 3 yield units.

All three additional admitted pivots are already labelled wrong in this synthetic cohort, while relevant-pivot count remains unchanged. This does not establish a population-level cost/quality rate, but it makes the controlled tradeoff explicit: the tested wider frontier performs more source work without adding a relevant labelled pivot.

## Consequences

Positive:

- graph-limit comparisons now include a bounded operational-work dimension;
- non-executing policy outcomes cannot be mistaken for provider cost;
- provider failures correctly consume request-cost units even though they yield no admitted pivot;
- the accounting remains deterministic, network-free and zero-spend.

Limits:

- request-cost units are not money;
- one successful fixture attempt currently contributes one observation-yield unit regardless of real provider payload size;
- source-specific rate limits, multi-request adapters and monetary pricing are not modelled;
- the synthetic cohort is not representative production evidence.

## Next review

Keep production recursion at depth 2 / 12 nodes. Before changing it, add consented or otherwise defensible labelled cases and, where useful, provider-specific request/yield weights. Do not convert these counters into identity probability or a universal provider-efficiency score.
