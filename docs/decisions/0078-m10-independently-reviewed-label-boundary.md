# ADR 0078 — Independently reviewed M10 labels stay separate from consent

Status: accepted

## Context

M10 previously recognized two label bases: synthetic regression fixtures and genuinely consented evidence. That was intentionally strict, but it left no truthful path for a label established through independent review of an external evidence record when consent was not the basis for that review.

Calling reviewed evidence `consented` would make the provenance record false. Treating it as synthetic would also discard a meaningful distinction.

## Decision

Add `independently_reviewed` as a third M10 label-provenance basis.

The label manifest counts synthetic, consented and independently reviewed fixtures and declared labels separately. It still stores only an opaque SHA-256 reference to the external evidence/review record; raw identifiers, source documents, consent material and review notes stay outside the experiment manifest.

Add a reviewed-only scenario-accounting boundary. It accepts a cohort only when every fixture is `independently_reviewed`, rejects synthetic, consented and mixed provenance, requires complete labels for every admitted pivot, and reports exact count fractions for the reviewed corpus.

Those fractions are descriptive within that corpus. They are not population false-positive/false-negative rates, calibration evidence, confidence or identity probability.

The existing consented-only analysis remains strict and unchanged: independently reviewed evidence does not satisfy its consent requirement.

## Consequences

Positive:

- M10 no longer needs to misuse the `consented` label when a defensible review basis exists;
- consented, reviewed and synthetic evidence remain distinguishable in replay identities and manifests;
- future reviewed cohorts can be evaluated without publishing raw review evidence or personal identifiers;
- scenario denominators stay explicit and tied to the exact replay.

Costs:

- an external review process still has to exist and be documented outside Git; this change does not manufacture reviewed labels;
- reviewed-corpus accounting remains descriptive and cannot support population claims without a defensible sampling design.

## Non-changes

- no production provider or network call changes;
- no recursion-limit change;
- no M5 weight, threshold, veto or calibration change;
- no raw consent/review evidence is retained in the repository;
- no independently reviewed cohort is created by this decision.
