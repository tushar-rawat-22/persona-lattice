# ADR 0034 — Reviewed upload identifiers may enter the typed lead path

Status: accepted for V2-D architecture closure

## Context

File preview already extracts normalized identifier candidates from bounded uploaded content, but extraction is intentionally inert. A prompt-like string inside a document must never become permission to query an external source.

The next V2-D step needs a narrow bridge from a human-reviewed upload candidate into the existing typed lead graph. The bridge must preserve provenance and must not create a second normalization or research-authorization policy.

## Decision

A document identifier can be promoted only after the existing review contract marks it `confirmed` and `external_research_authorized=true`.

`promote_confirmed_identifier_candidate()` then:

- rechecks the existing research-authorization invariant;
- accepts only currently executable identifier kinds: username, email, phone and URL;
- reuses `canonicalize_lead()` and therefore M1 identifier normalization;
- emits `LeadDisposition.AUTO_PIVOT` only because the separate human-review step has already cleared the review boundary;
- records `LeadReason.REVIEWED_DOCUMENT_IDENTIFIER` rather than pretending the identifier came from a public-provider field;
- carries the artifact ID and candidate ID in an `artifact://` source locator;
- carries the extracted-text character span when it is known;
- performs no provider call and does not itself enqueue or execute the lead.

Rule-based extraction now records deterministic character offsets for identifier candidates. Candidate span fields fail closed when only one offset is supplied or the range is invalid.

## Rejected alternatives

### Let extraction emit executable leads directly

Rejected. Uploaded content is untrusted data, and document text may contain instructions or misleading identifiers.

### Treat reviewed document identifiers as existing `PUBLIC_*` lead reasons

Rejected. That would misstate provenance. A reviewed upload is operator-supplied evidence, not a public-provider observation.

### Allow names and organizations to become research seeds after one confirmation

Rejected for this boundary. Current automatic research supports username, email, phone and URL seeds. Contextual names and organizations require a separate policy decision rather than an implicit expansion here.

## Current limitation

The present extractor returns one flattened text string. Character offsets are therefore available, but PDF page boundaries are not yet represented in the extraction contract and `source_page` remains unset. The operator/API wiring must not claim page-level provenance until extraction emits trustworthy page spans.

This ADR does not close that gap. The next document-intake block should add structured page-span provenance for PDFs before the reviewed-lead path is exposed as a complete operator workflow.

## Consequences

Positive:

- reviewed upload identifiers can use the same typed lead contract as provider-derived clues;
- extraction remains inert until explicit review;
- promoted leads retain artifact/candidate provenance without copying document text into the lead object;
- rejected and claim candidates remain non-executable;
- no new provider, credential, paid dependency or network path is introduced.

Cost:

- PDF page provenance still needs an extraction-contract change before the document workflow can be considered complete;
- promotion is currently an in-process contract, not a new API endpoint or automatic scheduler action.
