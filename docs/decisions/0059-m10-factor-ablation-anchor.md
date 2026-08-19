# ADR 0059 — Anchor M10 factor ablations to replay and M5 policy identity

Status: accepted for M10 evaluation support

## Context

M10 can now fingerprint the exact labelled graph cohort and frontier comparison used in a controlled run. Factor ablations are the next evaluation step, but an omission result is not reproducible if it is described only as “remove factor X.” The result also depends on the exact M5 weights, thresholds, independence requirements, strong-factor vocabulary and veto vocabulary in force for the run.

There is a second risk: omitting `hard_contradiction` is useful as a diagnostic sensitivity test, but it removes a safety veto. An experiment that does that must never be mistaken for an authorized production policy candidate.

## Decision

Add a versioned `M10FactorAblationPlan` that is anchored to both digests from an existing `M10ReplayRecord` and to a separate digest of the exact current M5 policy constants.

The plan creates one deterministic omission scenario for each current `FactorKind`. Every scenario is marked diagnostic-only. Scenarios that omit a veto factor are additionally marked safety-critical.

The policy digest covers:

- M5 policy version;
- every factor weight;
- possible-match and strong-candidate thresholds;
- minimum strong independence groups;
- strong-factor vocabulary;
- veto-factor vocabulary.

The plan digest covers the replay input/result identities, policy identity and exact ordered scenario manifest.

## What this does not do

This block does not execute ablations, score candidates, change factor weights, change thresholds or modify production M5 behavior. It does not create a new evidence store or retained personal-data surface.

In particular, a safety-critical diagnostic scenario is not a proposal to remove a production veto. Any later execution layer must use the real M5 engine rather than implementing a second correlation policy in M10.

## Consequences

A future ablation result can be tied to the exact labelled frontier replay and exact M5 policy that produced it. If fixture truth, frontier behavior, M5 weights, thresholds or factor vocabularies change, the corresponding experiment identity changes rather than silently reusing an old description.

The next M10 block can execute these scenarios against controlled M5 fixtures through the production correlation engine and record result deltas without changing production policy.
