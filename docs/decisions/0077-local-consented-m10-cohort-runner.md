# ADR 0077 — Real consented M10 labels enter through a local bounded runner

Status: accepted

## Context

M10 can already replay labelled graph fixtures and compute consented-only scenario accounting, but the only practical way to use that machinery was to construct Python fixtures in the repository. That is unsuitable for real consented cases: their identifiers and external consent records do not belong in Git, CI logs or public fixtures.

The current provenance vocabulary has `synthetic` and `consented` bases only. It does not have a separate independently-reviewed basis, so this runner must not silently classify reviewed-but-not-consented evidence as consented.

## Decision

Add a local JSON runner that converts a bounded private consented cohort file into the existing `M10GraphFixture` and consented-provenance contracts, executes the existing production `LeadFrontier` comparison, and returns aggregate counts plus replay/provenance digests only.

The runner:

- reads at most 1 MiB of UTF-8 JSON;
- accepts at most 256 fixtures and 2,048 declared nodes;
- requires one lowercase SHA-256 external consent-record reference per fixture;
- treats every imported fixture as consented and delegates completeness checks to the existing consented-analysis boundary;
- canonicalizes seed and lead identifiers through the same M1-backed lead normalization used by the graph;
- only allows child nodes beneath the seed or an earlier successful automatic pivot;
- evaluates the current production depth-2 / 12-node policy against the existing depth-3 / 12-node diagnostic candidate;
- prints no seed values, lead values, source locators, fixture names, cohort name or raw external consent records;
- returns one generic validation error at the CLI boundary so malformed private values cannot leak through exception text.

The private input file is not persisted by PersonaLattice. The output carries a digest of the input bytes, a digest of the cohort name, the existing M10 replay digests, the label-manifest digest, the analysis digest and aggregate scenario accounting.

## Boundaries

This runner does not make a cohort representative, calibrated or suitable for population error-rate claims. It does not verify the substance of consent; the external consent record remains outside the repository and must be reviewed separately. A bare unsalted hash of an email address, phone number or other low-entropy identifier is not an acceptable consent record.

If PersonaLattice later needs independently reviewed labels without consent, that requires an explicit provenance basis and analysis contract rather than reusing `consented` as a convenient bucket.

The runner does not alter production recursion, M5 factor weights, thresholds, vetoes, provider execution or retained case data.

## Consequences

A real consented cohort can now be evaluated locally without turning private identifiers into repository fixtures. M10 can advance on actual consented evidence when such a cohort exists, while CI continues to use synthetic structural tests only.
