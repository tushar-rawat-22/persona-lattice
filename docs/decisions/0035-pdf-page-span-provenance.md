# ADR 0035 — PDF page provenance comes from extraction-time spans

Status: accepted for V2-D document-intake closure

## Context

The bounded upload extractor already returned flattened PDF text and rule-based identifier candidates already kept global character offsets. Page numbers were intentionally left unset because a page number cannot be reconstructed reliably from the flattened string after page boundaries have been discarded.

The next operator review workflow needs defensible document provenance: a candidate should name a page only when the extractor can prove which page produced the exact character interval.

## Decision

PDF extraction now emits a structured `PageTextSpan` for every parsed page. Spans use one-based page numbers and half-open global character intervals `[source_start, source_end)` inside the exact flattened `extracted_text` returned by the extractor.

Pages are flattened with exactly one newline separator between page texts. The separator is not owned by either page. Empty pages therefore remain visible as zero-length spans, and their separators still count toward the extracted-text output limit.

Identifier candidates receive `source_page` only when their complete source interval is contained by exactly one page span. A match that crosses a page boundary keeps its global character offsets but leaves `source_page` unset. No heuristic page inference is permitted.

Normalized duplicate identifiers continue to collapse to one review candidate under the existing candidate contract. The retained provenance is the first matching occurrence, which is deterministic under the current extractor ordering. This block does not introduce an occurrence-list contract.

`ArtifactPreview` exposes the page-span map and validates that:

- page numbers are contiguous and one-based;
- page intervals match the flattened text cursor exactly;
- page separators account for exactly one character between pages;
- the final page interval ends at the extracted-text boundary;
- page spans appear only for `pypdf_text` extraction.

## Boundary correction

The previous PDF output-limit check counted only page text, while the returned flattened value also inserted newline separators. The output limit now covers the actual returned string, including those separators.

## Consequences

Positive:

- candidate page attribution is mechanically derived rather than guessed;
- global offsets and page numbers refer to the same extracted string;
- empty pages cannot silently shift later page attribution;
- cross-page matches fail closed to unknown page instead of receiving a false page number;
- the operator can inspect the page map without retaining another copy of uploaded content.

Costs:

- PDF preview responses gain a small page-span structure;
- a duplicate normalized identifier still retains only its first occurrence until a separately reviewed occurrence-provenance contract exists;
- page attribution describes pypdf text extraction order, not visual PDF coordinates or OCR geometry.

## Deliberately unchanged

- no OCR or new parser is added;
- no file is retained after preview processing;
- uploaded content remains untrusted and cannot authorize research;
- human confirmation remains required before candidate promotion;
- no provider/API, credential, paid service, recursion-limit or identity-semantic change is introduced.

## Next gate

Expose the existing reviewed-candidate promotion action through the private operator/API workflow using these exact page/offset provenance fields. Do not let the browser or uploaded text manufacture authorization state.