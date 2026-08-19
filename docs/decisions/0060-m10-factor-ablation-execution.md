# ADR 0060 — M10 factor ablations execute through the real M5 engine

Status: accepted for M10 evaluation

## Context

ADR 0059 made factor-ablation experiments reproducible by anchoring them to an exact M10 replay and exact M5 policy. It deliberately stopped before execution.

The next step must measure what happens when one M5 factor is omitted. Reimplementing weights, thresholds, vetoes or independence-group rules inside M10 would create a second scoring engine that could drift from production. A single synthetic case containing every factor is also insufficient: a hard contradiction veto would mask the effect of positive-factor omissions.

`CorrelationEngine` persists correlation runs as part of normal product behavior, so an evaluation harness must also avoid leaving diagnostic ablation runs in the supplied evidence database.

## Decision

M10 factor-ablation execution changes only the `CorrelationRequest.factors` tuple and evaluates the baseline and each omission through the production `CorrelationEngine`.

The execution layer:

- validates the replay/policy-anchored ablation manifest before running;
- requires named controlled cases with at least two factors;
- records baseline M5 outcome, evidence score and positive independence-group count;
- records the same fields after each planned factor omission plus deterministic deltas;
- marks omissions of factors absent from a case as explicit no-op scenarios rather than inventing an effect;
- preserves the manifest's `diagnostic_only` and `safety_critical` flags;
- never contains its own M5 weights, thresholds, veto logic or score calculation;
- executes each correlation inside a nested transaction and rolls that savepoint back, so diagnostic `CorrelationRun` and factor rows are not retained.

Controlled cases should separate positive-factor sensitivity from veto sensitivity. A veto-removal result can describe what the current engine would do without that input; it is not authorization to remove the veto from production.

## Consequences

Positive:

- M10 measures the implementation that actually runs in production;
- a future M5 policy change invalidates stale ablation manifests before execution;
- score and outcome changes are attributable to one omitted factor kind at a time;
- diagnostic evaluation does not expand retained case data;
- positive-factor and contradiction-veto behavior can be examined without one masking the other.

Costs and limits:

- controlled synthetic fixtures are still not population-level calibration evidence;
- the harness reports deterministic score/outcome sensitivity, not false-positive probability or causal importance;
- an omitted factor that is absent from a given case is a no-op for that case;
- the current execution report is in-memory evaluation output and is not a product-retained case schema.

## Production boundary

This decision changes no M5 factor weight, threshold, veto, calibration status or identity semantics. Production recursion remains depth 2 / 12 nodes. All ablations remain diagnostic-only, and hard-contradiction omission remains safety-critical.
