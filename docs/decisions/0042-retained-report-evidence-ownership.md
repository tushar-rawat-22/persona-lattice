# ADR 0042 — Retained quick-report evidence has one full-payload owner

Status: accepted for V2-D closure

## Context

A retained quick case stored each provider observation at the report root and then copied the same complete observation into `structured_report.source_evidence`. Account-candidate and contradiction sections copied those evidence objects again. A single public provider payload could therefore be retained two or three times inside one case.

The copies were convenient for presentation, but they had no independent evidence authority. They increased retained personal-data surface, serialized case size and the number of places that must remain consistent when evidence changes.

## Decision

`QuickResearchReport.observations` remains the canonical retained owner for complete quick-research provider evidence.

`build_structured_report()` now produces `private-evidence-report-v2` and must not copy complete observations. It keeps:

- aggregate counts and source names;
- the existing bounded `connected_identifiers` operator index for selected explicit public fields;
- observation indexes identifying account candidates and contradictions;
- coverage gaps and interpretation text.

The structured report no longer retains:

- a second seed object;
- `source_evidence` copies;
- copied `public_account_candidates` evidence objects;
- copied `contradictions` evidence objects.

The connected-field index remains a deliberate small projection because the current private operator UI uses it for direct navigation. It may repeat an explicitly selected public field and its source locator, but it cannot copy arbitrary provider payload fields. Full provider payload ownership stays with `observations`.

## Invariants

- an arbitrary provider-detail field that is not in the connected-field allowlist appears once in a retained quick report;
- account/contradiction classification references canonical observations by index;
- structured-report construction cannot become a second generic evidence store;
- identity probability remains disabled and identity claims remain false;
- converged-report retention is unchanged by this decision.

## Consequences

Existing private quick cases remain readable because retained JSON is not migrated in place. New cases use report version v2. The private UI already consumes the summary and connected-field projection and does not depend on the removed full-evidence sections.

A later closure audit may replace the remaining connected-field value/locator projection with canonical-observation references if that can be done without making the operator contract less clear. That is a separate compatibility decision; it is not a reason to retain full provider payload copies today.
