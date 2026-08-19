# ADR 0062 — M10 label provenance must be explicit before error analysis

Status: accepted

## Context

M10 can replay labelled synthetic graph fixtures and controlled M5 ablation cases deterministically. That is enough to test scheduler and scoring behavior, but it is not enough to support false-positive, false-negative or threshold claims.

The missing distinction is ground-truth provenance. A synthetic relevance label and a label backed by explicit consent are not interchangeable evidence bases. Without an explicit contract, a future evaluation could accidentally aggregate both and present a synthetic regression result as if it were consented evidence.

Raw consent material also does not belong in an experiment manifest. Storing names, emails, phone numbers, consent text or source documents again would expand the retained personal-data surface for no evaluation benefit.

## Decision

Add a replay-anchored M10 label manifest.

Each fixture must have exactly one label-provenance record with:

- the fixture name;
- a basis of `synthetic` or `consented`;
- an opaque lowercase SHA-256 digest referring to an external label/consent record.

The manifest:

- replays the supplied fixture cohort and fails closed if its input or result digest does not match the supplied `M10ReplayRecord`;
- requires exact fixture/provenance coverage with no missing, duplicate or extra records;
- fingerprints the replay identity, label basis, evidence digest and exact pivot relevance labels;
- keeps synthetic and consented fixture/declared-label counts separate;
- returns count-only corpus metadata and does not calculate rates, confidence, probability or calibration.

The declared-label counts describe labels present in fixture definitions. They are not scenario-specific admitted-pivot denominators. Future error analysis must combine provenance with the actual scenario execution counters rather than treating every declared fixture label as an evaluated prediction.

The evidence digest is a reference, not proof by itself. It must refer to a privacy-safe external record; it must not be a bare hash of a personal identifier. The underlying consent or label evidence remains outside this public-safe experiment manifest and must be reviewed under the appropriate data-handling rules.

## Consequences

M10 can now prove which labelled cohort definition and provenance class produced a replay. Future false-positive/false-negative analysis has a place to enforce defensible evidence bases instead of inferring them from fixture names or comments.

Synthetic fixtures remain useful for regression and adversarial testing, but their labels cannot silently become consented ground truth.

This change does not add real personal data, change production recursion, alter M5 weights/thresholds/vetoes, activate a provider, or create identity probability.

## Next gate

Broaden M10 only with label sets that can satisfy this provenance contract. False-positive/false-negative or threshold analysis should be added only when a sufficiently sized consented or otherwise separately reviewed labelled cohort exists; synthetic-only counts remain diagnostic.