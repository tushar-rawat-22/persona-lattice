# ADR 0007 — explainable evidence correlation before probability

## Status

Accepted for M5 implementation.

## Context

M4 can produce public account candidates from confirmed usernames, but the
existence of the same handle on another site is weak evidence. M5 needs a way to
combine supporting and contradictory evidence without turning a convenient
heuristic into a false identity probability.

Record-linkage systems commonly distinguish model/link evaluation from cluster
evaluation, and meaningful threshold evaluation requires labelled ground truth.
PersonaLattice does not yet have a lawful, reviewed labelled identity benchmark.
That means an empirical calibration claim would be premature.

## Decision

M5 begins with a deterministic evidence-strength policy rather than a trained or
probabilistic identity model.

1. Correlation runs and factor records are persisted in their own ORM domain,
   separate from `Claim` and `Observation`.
2. Every factor must reference stored evidence belonging to the subject.
3. Same-username evidence has deliberately low weight and cannot be upgraded to
   exact confirmed identifier overlap.
4. Exact confirmed identifier overlap rejects username identifiers; username
   reuse remains the weaker dedicated factor.
5. Positive factors in the same declared source-independence group do not stack.
   Only the strongest contribution from that group is applied.
6. Stale source observations remain visible in the result but contribute zero
   under policy version `m5-evidence-strength-v1`.
7. A hard contradiction is a veto and produces `contradicted` even when weaker
   positive evidence is present.
8. A `strong_candidate` requires a score threshold, at least two independent
   positive evidence groups, and at least one strong factor type.
9. The result always carries `calibration_status=uncalibrated` and
   `is_identity_claim=false`.
10. Canonical input/output JSON and SHA-256 digests make replays deterministic;
    an identical request reuses the persisted run instead of generating a new
    decision record.
11. M5 performs no provider/network call and does not invoke AI, ML, embeddings
    or biometric comparison.

## Initial factor vocabulary

- same username;
- exact confirmed non-username identifier overlap;
- independent public cross-link;
- compatible public profile metadata;
- temporal compatibility;
- hard contradiction.

The vocabulary and weights are versioned policy. Adding a factor or changing a
weight requires a new policy version and review rather than silently changing
historical interpretation.

## Why not call the score a probability?

A weighted rule score can rank evidence without being statistically calibrated.
A probability claim would require labelled ground truth, an evaluation design,
measured error trade-offs and calibration analysis appropriate to the intended
use. Until that exists, the output is an evidence-strength triage state only.

## Consequences

- M5 is less glamorous than an ML matcher but much easier to audit and falsify.
- Weak repeated sources cannot manufacture confidence through duplication.
- Strong contradictions are not averaged away.
- Future probabilistic linkage remains possible, but it must earn that status
  through a separate evaluation and calibration gate.
