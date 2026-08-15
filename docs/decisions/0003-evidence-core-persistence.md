# ADR 0003 — evidence core persistence

**Status:** accepted for M1

PersonaLattice stores evidence as relational records before introducing live
provider integrations.

## Decision

The M1 persistence layer uses SQLAlchemy 2.0 with a SQLite test/development
backend and database-agnostic UUID columns. The model is intentionally simple
enough to move to PostgreSQL later without changing the evidence concepts.

The five core records are:

- `Subject` — the case entity being researched;
- `Identifier` — a normalized phone, email, username, URL, name or organization;
- `Observation` — exactly what a real source returned, with provenance and time;
- `Claim` — a human, rule-based or AI-derived statement about the subject;
- `EvidenceLink` — an explicit support, contradiction or unresolved relationship
  between a claim and an observation.

## Boundaries

AI may create or revise a `Claim`. AI may not be recorded as an
`ObservationSourceKind`. That keeps model reasoning separate from source
evidence.

Identifiers keep the raw input, a normalized display value and a comparison
key. Deduplication uses the comparison key; the raw value is retained for
auditability.

Generic normalization is deliberately conservative. Email local-part case,
username case, and URL path/query/fragment semantics are preserved because their
equivalence can be provider-specific. Provider adapters may add stricter
canonicalization later when a platform's rules justify it.

Observations carry `retrieved_at` and optional `expires_at` timestamps. Missing
expiry means freshness is unknown rather than permanent.

SQLite foreign-key enforcement is enabled explicitly in the database factory so
tests exercise the same referential assumptions expected from PostgreSQL.

## Deferred

M1 does not add:

- provider calls;
- migrations tooling;
- production database credentials;
- vector search;
- automated entity resolution;
- AI execution.

Those arrive only after the evidence invariants are stable.
