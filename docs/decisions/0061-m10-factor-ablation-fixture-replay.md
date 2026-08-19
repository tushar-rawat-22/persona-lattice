# ADR 0061 — Controlled M5 ablation fixtures have UUID-independent replay identity

Status: accepted for M10 evaluation

## Context

ADR 0060 executes controlled factor omissions through the production `CorrelationEngine`, but the first controlled cases were assembled inside a test helper using freshly generated subject, identifier and observation UUIDs. The observed score/outcome deltas were deterministic, yet the case definitions themselves had no stable identity that could be reconstructed and compared across separate databases.

Hashing a `CorrelationRequest` directly would not solve that problem because its subject, candidate, observation and identifier references are database-generated IDs. Those IDs identify one materialization, not the semantic experiment definition.

## Decision

Define the controlled M5 ablation cohort as a versioned semantic fixture set before it is materialized into evidence rows.

The semantic definition records only experiment-relevant inputs:

- case name and candidate handle;
- ordered factor kinds;
- support-source names for non-candidate factors;
- confirmed identifier kind/value where exact-identifier overlap requires one;
- the controlled evaluation timestamp;
- a fixture schema version that must change if implicit materialization semantics change.

The fixture digest canonicalizes independent top-level case ordering but preserves factor ordering within each case because M5 receives an ordered factor tuple. Generated subject, identifier, observation and correlation-run UUIDs are excluded.

A materializer converts the validated semantic fixture set into fresh `EvidenceStore` rows and `CorrelationRequest` objects for the real engine. The previous test-local case builder is removed so there is one reusable controlled case definition.

After execution, M10 can also build a result replay record containing:

- the exact factor-ablation plan digest;
- the semantic fixture digest;
- a deterministic digest of baseline and ablated outcomes, scores, independence-group counts and scenario metadata.

The result digest excludes database/run UUIDs and canonicalizes case/scenario ordering that does not change independent case semantics.

## Consequences

Positive:

- reconstructing the same controlled cohort in a fresh database yields the same fixture identity;
- generated UUID changes cannot make the experiment look different;
- semantic changes such as a candidate handle, factor order, source name or confirmed identifier change the fixture digest;
- controlled M5 case definitions no longer live only inside one test file;
- result replay identity can be compared across reconstructed runs without retaining diagnostic M5 rows.

Costs and limits:

- the fixture schema version now carries responsibility for implicit materialization rules such as synthetic source kinds, timestamps relative to evaluation time and source-locator construction;
- this remains synthetic controlled evaluation, not calibration or population evidence;
- result replay identity proves deterministic experiment/result identity, not correctness, accuracy, confidence or causal factor importance.

## Production boundary

This changes no M5 weight, threshold, veto, retention rule, provider behavior or production recursion limit. Production remains depth 2 / 12 nodes, M5 remains uncalibrated, and hard contradiction remains a safety-critical production veto.