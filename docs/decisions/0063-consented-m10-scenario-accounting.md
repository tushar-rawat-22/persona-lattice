# ADR 0063 — Consented M10 analysis uses admitted scenario denominators

Status: accepted for M10 evaluation infrastructure

## Context

M10 can now bind each labelled graph fixture to either synthetic or consented label provenance and to an exact deterministic replay. That is necessary but not sufficient for error-style analysis.

The existing synthetic cohort contains useful regression labels, but those labels are not consented ground truth. Its declared label totals also are not automatically the denominator for a particular frontier policy because a policy may never admit some labelled pivots.

Using the synthetic corpus to publish a false-positive rate, false-negative rate or calibration claim would therefore overstate what the data supports.

## Decision

Add a separate consented-cohort analysis boundary that refuses to run unless:

- every fixture in the replay is labelled with `consented` provenance;
- the label manifest exactly matches the replayed fixture cohort;
- every pivot admitted by each evaluated scenario has an explicit label;
- replay and label-manifest identities remain part of the analysis identity.

For each scenario the analysis records exact counts for:

- declared relevant and wrong labels in the consented fixture corpus;
- admitted relevant and wrong pivots;
- relevant labels not admitted by that scenario;
- wrong labels not admitted by that scenario.

It also records two exact count fractions:

- wrong admitted pivots / all labelled admitted pivots;
- admitted relevant pivots / all declared relevant pivots.

The implementation stores numerator and denominator rather than a float or percentage. A zero denominator produces no fraction rather than a fabricated zero rate.

## Interpretation boundary

These fractions describe one declared consented fixture cohort under one deterministic frontier policy. They are not population-level false-positive/false-negative rates, model calibration, confidence, identity probability or evidence that the cohort is representative.

A later threshold/error-analysis block may introduce stronger terminology only if the consented cohort definition and denominators actually justify it.

## Privacy boundary

The analysis consumes the existing opaque SHA-256 references to external consent/label records. It does not retain raw consent text, personal identifiers or source documents.

## Consequences

Positive:

- synthetic regression labels cannot accidentally enter consented error-style accounting;
- scenario-specific admitted denominators are explicit;
- unlabelled admitted pivots fail closed instead of disappearing from a rate;
- analysis identity is anchored to both replay and label-provenance manifests.

Costs:

- the current synthetic six-fixture cohort remains ineligible for this analysis;
- no real-world metric is produced until a genuinely consented or equivalently defensible labelled cohort exists.

## Production impact

None. Production recursion remains depth 2 / 12 nodes. M5 remains uncalibrated evidence-strength triage with `is_identity_claim=false`. No provider, credential, paid dependency or retained personal-data surface changes in this decision.
