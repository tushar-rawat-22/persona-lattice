# ADR 0045 — Quick connected fields reference canonical observations

Status: accepted for V2-D privacy closure

## Context

`private-evidence-report-v2` keeps complete provider payloads in top-level quick observations. After PR #72, the structured report stopped copying complete evidence sections, but `connected_identifiers` still retained selected field values plus the provider source and source locator so the private operator UI could render a compact navigation index.

That projection was narrow, but it still duplicated personal/public identifier values and provenance already owned by the canonical observation. The UI requirement does not require those copies to exist in SQLite.

## Decision

New structured quick reports retain connected fields as references only:

- connected-field kind;
- zero-based canonical observation index;
- the exact reviewed observation detail field;
- the existing display status.

The canonical observation remains the sole retained owner of the field value, provider source and source locator.

`CaseStore` resolves new references only when returning a case to the API/UI. This compatibility projection is transient and is never written back to retained storage. Cases written before this ADR already contain the old bounded value/source/source-locator projection and remain readable without migration.

Reference hydration fails closed when the kind/field pair is not one of the reviewed connected-field mappings, the observation index is malformed or out of range, the canonical observation/provenance shape is invalid, or the referenced field no longer contains a usable value.

## Consequences

Positive:

- selected connected values and provider locators now have one retained owner;
- the existing private UI remains compatible without a storage migration;
- the structured report still provides deterministic navigation intent;
- malformed retained references cannot silently resolve to unrelated evidence.

Costs:

- `CaseStore` temporarily owns another read-time compatibility projection;
- the private UI still consumes hydrated legacy-shaped connected-field objects rather than resolving references itself.

## Next review

When the private operator UI is updated for V2-D closure, make it resolve connected fields directly from canonical observations and remove this temporary response hydration path. Keep read-only compatibility for historical retained cases only if needed; do not rewrite old case JSON solely for schema cleanup.
