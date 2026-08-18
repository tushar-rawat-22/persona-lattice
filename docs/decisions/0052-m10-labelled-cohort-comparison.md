# ADR 0052 — M10 graph-limit evaluation uses labelled fixture cohorts

Status: accepted for M10 evaluation foundation

## Context

PersonaLattice already compares recursion policies with deterministic labelled graph fixtures running through the real `LeadFrontier`. A single fixture is useful for proving scheduler behavior, but it is too easy to over-read one topology as representative evidence for a production limit change.

M10 needs a way to compare the same candidate frontier policy across several independent synthetic or consented fixture families without inventing reliability percentages, confidence scores or identity probabilities.

## Decision

Add a cohort comparison layer on top of the existing graph-limit evaluator.

Each cohort fixture has:

- a unique human-readable name;
- one seed kind/key;
- deterministic emitted leads and provider-failure facts;
- optional explicit `relevant` / `wrong` labels for successful pivots.

Every scenario still runs each fixture through `evaluate_graph_limit_fixture()`, which uses the production `LeadFrontier` policy. The cohort layer only aggregates deterministic counts across fixtures and reports candidate-minus-baseline deltas.

Current cohort outputs include fixture/node counts, maximum observed depth, duplicate suppression, provider failures, budget stops, labelled admitted pivots, wrong/relevant pivots and unlabelled admitted pivots.

The layer deliberately does not:

- calculate a provider reliability percentage;
- calculate a wrong-pivot probability or confidence interval;
- recommend a production recursion limit;
- change M5 thresholds or calibration status;
- call any network source.

Empty cohorts, duplicate fixture names and duplicate scenario names fail closed. Existing fixture-truth validation remains authoritative rather than being reimplemented in the cohort layer.

## Consequences

M10 can now compare one frontier-policy change across more than one graph shape and see whether extra capacity consistently adds useful labelled pivots or simply creates more wrong pivots and traversal cost.

The initial regression cohort covers three deliberately different conditions: a depth-limited chain, duplicate-heavy output and a provider failure. That is a foundation, not representative calibration evidence. Broader fixtures across additional lead kinds and source-yield/cost conditions are still required before changing production depth or node limits.

Production recursion therefore remains depth 2 / 12 nodes.

## Next work

Broaden the labelled cohort, add deterministic replay/factor-ablation coverage, and measure source-yield/cost implications before proposing any frontier-limit or correlation-threshold change. New external-source activation remains a separate reviewed workstream.
