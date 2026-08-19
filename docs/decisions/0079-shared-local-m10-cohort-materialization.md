# ADR 0079 — Local M10 evidence cohorts share one materialization boundary

Status: accepted

## Context

The consented M10 runner already had a bounded private JSON parser and fixture materializer. After independently reviewed labels gained their own provenance and analysis boundary, copying that parser into a second runner would create two normalization, graph-shape and privacy contracts that could drift.

The evidence basis also must not be selected by the private input file. A cohort file claiming that it is `consented` or `independently_reviewed` is not evidence that the claim is true.

## Decision

Extract the private local JSON parsing and `M10GraphFixture` materialization into one shared module.

The consented runner calls that materializer with `M10LabelBasis.CONSENTED`. The reviewed runner calls it with `M10LabelBasis.INDEPENDENTLY_REVIEWED`. Synthetic provenance is rejected by the local evidence-backed materializer.

The input schema does not carry provenance authority. Top-level or fixture-level `basis` / `label_basis` fields are rejected. The executable entry point fixes the basis before the file is parsed into provenance records.

Both runners keep the existing limits and M1-backed normalization path, use the same production-vs-diagnostic frontier scenarios, and return only aggregate accounting plus cryptographic experiment digests. Their CLI failures remain intentionally generic.

## Consequences

Positive:

- consented and reviewed evidence use one parser, graph-shape contract and normalization path;
- future parser/privacy fixes apply to both evidence-backed runners;
- a private JSON file cannot upgrade its own provenance basis;
- the existing consented runner remains a strict consent-only entry point;
- reviewed evidence gets a practical local ingestion path without entering repository fixtures.

Costs:

- the shared materializer becomes security/privacy-sensitive infrastructure and requires regression coverage whenever the local cohort schema changes;
- the two runners still have small separate wrappers so operator intent remains explicit rather than being chosen by an input flag.

## Non-changes

- no real consented or reviewed cohort is added;
- no production provider, source, recursion policy or M5 behavior changes;
- no raw consent/review record or private identifier is retained in Git or CLI output;
- reviewed evidence is not consent, and neither evidence basis becomes calibration or population-performance evidence by passing its local runner.
