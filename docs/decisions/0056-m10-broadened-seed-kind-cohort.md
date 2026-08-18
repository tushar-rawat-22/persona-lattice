# ADR 0056 — Broaden M10 across seed kinds before changing recursion

Status: accepted for M10 evaluation support

## Context

The first M10 cohort used three username-seeded fixtures. That was enough to show that one deeper synthetic path could add a wrong pivot, but it was too narrow to support conclusions about email-, URL- or reviewed-phone-seeded research.

The cohort aggregate also omitted review/display/blocked decision counts even though those states are part of the production frontier policy. That made the aggregate less useful for evaluating higher-sensitivity lead behavior.

## Decision

Add a reusable deterministic synthetic cohort spanning username, email, URL and reviewed-phone seeds. The cohort exercises:

- depth-limited traversal;
- duplicate suppression;
- provider failure;
- email → URL → username traversal;
- URL traversal with a review-only phone clue;
- reviewed-phone seed traversal.

Extend `M10CohortCounters` and `M10CohortDelta` with review-required, display-only and blocked counts so non-executing policy decisions are not lost during aggregation.

The fixture library is evaluation support only. It does not call providers, change source activation, alter the production scheduler or claim that the synthetic cohort is representative of real investigations.

## Result

Under the broader synthetic cohort, the current depth-2 / 12-node policy admits 9 labelled pivots: 8 relevant and 1 wrong. The depth-3 / 12-node candidate admits three additional labelled pivots, all three labelled wrong in these fixtures, while adding no relevant pivot.

That result is a controlled fixture outcome, not population evidence. It strengthens the reason to keep production at depth 2 / 12 nodes, but it does not establish an optimal frontier policy.

## Consequences

Positive:

- M10 no longer relies on username-only seed shapes;
- review-only behavior is visible in cohort totals;
- future graph-limit comparisons can reuse the same multi-kind synthetic cohort;
- the result remains deterministic and network-free.

Limits:

- this cohort still does not model provider request-cost units or monetary cost;
- it does not establish provider reliability rates;
- it does not replace consented labelled evaluation data;
- factor replay/ablation and threshold analysis remain separate work.

## Next review

Add explicit source-attempt/yield cost accounting for evaluation fixtures before using M10 to reason about the operational cost of larger frontier policies. Keep production recursion unchanged until broader labelled evidence supports a change.
