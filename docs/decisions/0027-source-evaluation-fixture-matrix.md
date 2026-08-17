# ADR 0027 — Source evaluation uses a complete deterministic state matrix

Status: accepted for V2-D evaluation instrumentation

## Context

The source-evaluation counters now distinguish completed lookups, attempted failures, local budget stops, optional-unconfigured sources and scheduler states. The existing tests covered representative examples, but they did not lock every current `SourceRunState` and `SourceRunReason` into one fixture.

That leaves a maintenance risk: a new state or reason could be added later without forcing the evaluation contract to decide whether it is an attempt, a completed attempt, a failed attempt or a non-attempt.

## Decision

Add one deterministic synthetic matrix that covers every current source-run state and every current reason at least once.

The matrix locks these invariants:

- `executed` and `not_found` are completed attempts;
- `execution_failure` and `remote_rate_limit` are attempted failures;
- local budget stops and optional-unconfigured sources are non-attempts;
- queued, review-required, display-only and blocked records are non-attempt scheduler/policy states;
- result observation counts are yield only, not evidence quality;
- aggregate and per-source evaluation are independent of input ordering;
- the complete current enum vocabulary must remain represented by the fixture.

If a future state or reason is added, the vocabulary-coverage test must fail until the evaluation semantics and fixture are updated together.

## Scope

This is test/evaluation infrastructure only. It does not add a provider, network call, credential, paid dependency, retained personal field, recursion capacity or identity interpretation.

## Consequences

Positive:

- source-state vocabulary changes cannot silently bypass evaluation review;
- provider failures remain separated from local policy and configuration states;
- graph and reliability work can build on a stable failure fixture rather than ad hoc examples;
- deterministic ordering remains an explicit contract.

Cost:

- any deliberate state/reason expansion now requires a matching fixture decision, which is intentional friction.

## Next gate

Add graph-growth, duplicate and wrong-pivot measurements over deterministic graph fixtures before changing recursion limits. Keep provider reliability percentages and calibrated identity claims out of scope until denominators and labelled data justify them.
