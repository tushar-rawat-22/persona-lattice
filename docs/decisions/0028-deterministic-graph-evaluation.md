# ADR 0028 — Graph evaluation uses structural counters plus explicit relevance labels

Status: accepted for V2-D architecture closure

## Context

The recursive frontier already records admitted pivots, duplicate suppression, provider failures and budget stops. Those facts can measure graph growth and duplicate behavior, but they cannot establish whether a pivot was substantively wrong. Inferring that from handle similarity, provider agreement, graph shape or M5 output would create an unreviewed identity classifier and an unauditable denominator.

## Decision

Add deterministic graph-evaluation counters over converged reports. They record nodes, added nodes, edges, maximum depth, terminal automatic lead decisions, admitted pivots, duplicate suppression, provider failures, budget stops and review/display/blocked states.

Wrong-pivot measurement is label-gated. An admitted child may be labelled `relevant` or `wrong` only by a deterministic synthetic fixture or an explicitly consented evaluation set. Labels are keyed to admitted child node keys; labels for non-admitted keys are rejected. The labelled-admitted count is exposed as the denominator. Unlabelled admitted pivots remain visible and unscored. No percentage or quality score is emitted here.

## Consequences

- structural graph growth and duplicate suppression use runtime facts only;
- wrong-pivot counts cannot exceed the explicit labelled set;
- unlabelled production research is not silently treated as correct;
- future recursion experiments have auditable denominators;
- no provider, network call, credential, paid dependency, retained identifier copy or identity probability is added.

## Next gate

Use deterministic graph fixtures to compare the existing depth/node ceilings under known relevant/wrong pivots. Keep depth 2 / 12 nodes unchanged until those fixtures show how added capacity changes graph growth and labelled wrong-pivot exposure.
