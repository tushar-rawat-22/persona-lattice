# Architecture

PersonaLattice separates **collection**, **evidence**, **reasoning** and
**presentation**. Mixing those layers would make false positives hard to
detect and license/privacy boundaries hard to enforce.

## System view

```text
┌────────────────────────────────────────────────────────────┐
│ Dashboard                                                   │
│ identifiers • notes • links • files • purpose • consent    │
└──────────────────────────────┬─────────────────────────────┘
                               │
┌──────────────────────────────▼─────────────────────────────┐
│ Intake + policy gate                                       │
│ normalization • purpose check • contact-risk restrictions  │
└──────────────────────────────┬─────────────────────────────┘
                               │
┌──────────────────────────────▼─────────────────────────────┐
│ Provider orchestration                                     │
│ phone • web • username • social • registry • documents     │
└──────────────────────────────┬─────────────────────────────┘
                               │
┌──────────────────────────────▼─────────────────────────────┐
│ Evidence store                                             │
│ source • observation • timestamp • provenance • freshness  │
└──────────────────────────────┬─────────────────────────────┘
                               │
┌──────────────────────────────▼─────────────────────────────┐
│ Correlation engine                                         │
│ candidate entities • contradictions • confidence factors   │
└──────────────────────────────┬─────────────────────────────┘
                               │
┌──────────────────────────────▼─────────────────────────────┐
│ AI analyst                                                 │
│ extraction • gap finding • explanation • summarization     │
│ NEVER a source of truth                                    │
└──────────────────────────────┬─────────────────────────────┘
                               │
┌──────────────────────────────▼─────────────────────────────┐
│ Report / graph                                             │
│ claims • confidence • supporting evidence • unresolved gaps│
└────────────────────────────────────────────────────────────┘
```

## Monorepo

### `apps/web`

Next.js dashboard. The browser should not hold provider secrets. It submits a
case to the API and renders normalized results, evidence and graph state.

### `services/api`

FastAPI service. It owns:

- input schemas;
- purpose/consent enforcement;
- provider orchestration;
- evidence normalization;
- correlation rules;
- report construction.

### Future packages

As the project grows we expect to split out:

- `packages/contracts` for versioned cross-service schemas;
- `packages/correlation` for deterministic scoring;
- `workers` for long-running provider/document jobs;
- `migrations` for PostgreSQL;
- `evals` for identity-resolution quality tests.

## Data model

### Subject

A case-level entity under investigation.

### Identifier

A phone, email, username, name, URL, organization or other candidate handle.

### Observation

Exactly what a source returned, with source, time, provenance and reliability
metadata.

### Claim

A statement derived from one or more observations, for example "these two
public accounts probably refer to the same person."

### Evidence link

The explicit relationship between a claim and the observations that support or
contradict it.

## AI boundary

Model output must never be written directly as an observation. Model output is
stored as a derived analysis object that references existing evidence IDs.

If a sentence cannot point to evidence, it does not belong in the final report
as a factual claim.

## Storage direction

Development can use SQLite for local iteration. Production should use
PostgreSQL with encrypted object storage for uploaded files. Raw provider
responses should have short retention and must never be committed to Git.

## Security direction

- secrets stay server-side;
- uploads are treated as untrusted;
- URL fetchers need SSRF protection;
- providers are allowlisted;
- case access is audited;
- exports are redacted by policy;
- raw evidence retention is configurable and short by default.
