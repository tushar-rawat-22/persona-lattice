# ADR 0029 — Graph-limit changes require labelled deterministic comparison

Status: accepted for V2-D architecture closure

## Problem

PersonaLattice currently caps convergence at depth 2 and 12 nodes. PR #44 added structural graph counters and label-gated wrong-pivot counts, but those counters alone do not show what a larger frontier would admit. A limit increase without a controlled comparison could reduce budget stops while also admitting more irrelevant pivots.

The production convergence path also used a private helper to translate the depth/node compatibility settings into `FrontierLimits`. An evaluation harness that recreated those limits independently could silently test a different scheduler policy.

## Decision

Move the private-V1 compatibility-limit constructor into `intelligence.frontier` and use that same function from production convergence and evaluation fixtures.

Add a network-free graph-limit evaluation harness that:

- runs deterministic fixture leads through the real `LeadFrontier` admission policy;
- supports successful synthetic pivots, duplicate suppression and provider-failure facts;
- accepts pivot relevance only as explicit `PivotRelevance` truth supplied by synthetic or explicitly consented evaluation data;
- filters labels to pivots actually admitted under each scenario;
- compares a named baseline with candidate `FrontierLimits` using count deltas only;
- reports added nodes, observed-depth change, duplicate-suppression change, budget-stop change, labelled-admission change and relevant/wrong-pivot exposure;
- emits no quality percentage, confidence score or identity probability.

A fixture label for an impossible result key, a non-enum label, contradictory failure/result facts or duplicate scenario names fails closed.

## Consequences

The current depth-2 / 12-node policy can now be compared against candidate policies without network calls or a production limit change. Because production convergence and the evaluation harness share the same compatibility-limit constructor, a policy-shape change cannot occur in only one of those paths.

A deterministic sample in the regression suite intentionally demonstrates the tradeoff rather than pretending larger is better: allowing depth 3 admits both an additional relevant pivot and an additional wrong pivot, while also changing duplicate and budget-stop counts. That fixture is a contract test, not evidence that depth 3 should be enabled in production.

## Out of scope

This decision does not change production recursion limits, provider/API coverage, M5 thresholds, identity semantics, credentials or retained personal-data fields. It does not establish a representative real-world error rate; that requires a defensible labelled evaluation set.

## Next review

Keep production at depth 2 / 12 nodes. Use this harness for additional synthetic/consented fixture families and only consider a runtime limit change after the labelled denominator, wrong-pivot exposure, graph growth and provider-cost implications are understood together.
