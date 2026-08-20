# ADR 0080 — Metadata-only retained-case index

## Problem

The private case navigator used `GET /v1/cases` to render a short recent-case list. That endpoint loaded complete retained reports from SQLite, including `report_json`, even though navigation only needs case identity, timestamps and the seed. Increasing the list size would therefore increase evidence deserialization and response payload for no operator benefit.

## Decision

`GET /v1/cases` is the authenticated metadata-only case index. Its response contains only `id`, `created_at`, `expires_at`, `seed_kind` and `seed_value`.

The storage path uses an explicit five-column `SELECT`; it does not select or decode `report_json`. Pages are bounded to at most 50 records and ordered by `(created_at DESC, id DESC)`. An opaque cursor carries the last `(created_at, id)` pair so continuation is deterministic when cases share a timestamp.

The next cursor is returned in `X-PersonaLattice-Next-Cursor`. Opening one case continues to use `GET /v1/cases/{case_id}`, which is the only navigation path that loads the retained report.

The private console consumes that cursor through one compact `Load older cases` action. Older pages append metadata-only summaries and are deduplicated by case ID. Refreshing after create/delete returns navigation to the newest page rather than retaining a stale cursor chain.

## Consequences

Malformed or unusually large retained report JSON cannot break or inflate case-index reads. Listing more case metadata does not deserialize the evidence payload. Authentication, privacy-safe audit events, expiry purge, explicit deletion and the 30-day default retention policy are unchanged.

Existing retained rows need no migration because the summary is projected from columns already present in `research_cases`. Historical report shapes remain readable through the existing single-case endpoint.

The old `CaseStore.list_recent()` full-report method remains available for internal compatibility, but the private navigation endpoint no longer uses it.

## Out of scope

This change does not add case search, export, bulk evidence loading, a new retained field, a source integration, an M5 semantic change or a recursion-policy change. The operator navigation remains deliberately simple: no infinite scroll and no decorative pagination framework.