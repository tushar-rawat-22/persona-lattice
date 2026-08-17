# ADR 0026 — Source evaluation starts with descriptive counters

Status: accepted for V2-D evaluation instrumentation

## Context

PersonaLattice now carries factual `SourceRunRecord` values from quick research into converged reports. That creates enough structured evidence to measure source behavior without reading warning strings or retaining another copy of identifiers and provider payloads.

The next temptation would be to publish provider "reliability scores" or percentages immediately. That would be premature. The current sample sizes are small, sources have different semantics, and a legitimate `not_found` result is not a provider failure. Local budget stops and optional-unconfigured sources also say nothing about upstream reliability.

## Decision

Add deterministic descriptive counters over `SourceRunRecord` values before adding ratios, thresholds or recursion changes.

The evaluation projection records, globally and per logical source:

- total source-run records;
- execution attempts;
- completed attempts;
- failed attempts;
- attempted outcomes not yet classified by the current vocabulary;
- result-bearing records and total admitted observation count;
- completed no-match results;
- remote rate limits;
- execution failures;
- local budget stops;
- optional-unconfigured states;
- queued, review-required, display-only and blocked states.

A completed no-match call counts as a completed attempt, not a failure. A local budget stop and an optional-unconfigured source do not count as attempts. Remote rate limits and proven execution failures do count as attempted failures.

The first version exposes counts only. It does not calculate provider success percentages, identity-quality scores, confidence, cost estimates or service-level claims.

## Privacy boundary

The evaluation projection is derived from the already privacy-bounded source-run contract. It does not contain identifier values, source locators, provider payloads, credentials, exception text or wall-clock traces.

Per-source grouping uses only the logical source name already present in the source-run record.

## Why counts before rates

A percentage can look authoritative with almost no evidence. Counts force the operator to see sample size and outcome composition before interpreting source behavior. Ratios may be added later only when the evaluation dataset and denominator semantics are explicit.

The `unclassified_attempt_count` is deliberate future-proofing. If a later source state proves execution was attempted but does not fit completed or failed semantics, evaluation must surface that mismatch rather than silently forcing it into a success/failure bucket.

## Consequences

Positive:

- recursion and provider decisions can be based on factual outcome counts rather than warning text;
- local policy stops no longer contaminate provider-failure measurements;
- `not_found` remains a valid completed lookup outcome;
- per-source comparisons retain their sample sizes;
- future state-vocabulary drift becomes visible through `unclassified_attempt_count`.

Costs:

- these counters are descriptive only and do not yet answer whether a source is "good";
- observation count is evidence yield, not evidence quality;
- graph-growth, wrong-pivot and labelled accuracy measurements still belong to M10-style evaluation.

## Next gate

Run these counters through deterministic synthetic/failure fixtures and use them as the measurement boundary for later graph-growth evaluation. Do not raise depth/node limits or publish provider reliability percentages from small uncontrolled samples.
