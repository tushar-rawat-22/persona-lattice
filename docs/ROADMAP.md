# Roadmap

PersonaLattice is an evidence-first private research workbench. The public deployment is a product preview; real intake, provider execution and retained case data belong to one authenticated operator account until a future decision explicitly changes that model.

## M0 — public foundation

**Status: complete**

- repository, license and source policy
- product architecture
- intake API
- dashboard shell
- CI
- continuity handover

## M1 — evidence core

**Status: complete**

- persistent subject/identifier/observation/claim/evidence-link schemas
- deterministic normalization outside the HTTP layer
- provenance and freshness model
- support/contradict/unresolved evidence relationships
- AI-claim/source-observation separation
- redaction utilities
- synthetic fixtures only

## M2 — safe file intake + extraction boundary

**Status: complete**

- bounded multi-file PDF/TXT upload
- filename, MIME and byte-level validation
- private UUID-named temporary staging and SHA-256 provenance
- isolated text extraction with resource/output ceilings
- deterministic review-only identifier candidates
- explicit human-confirmation gate before any later external query
- prompt-like uploaded content kept inert as untrusted data

## M3 — provider framework and governed execution

**Status: complete**

- versioned provider request/result/error contracts
- purpose/consent/provider-status/contact-risk enforcement immediately before execution
- source/auth/resource metadata in the provider registry
- bounded retries, rate budgets, concurrency, timeouts and response-size ceilings
- server-side secret resolution
- public-safe provider-log redaction
- provenance-bearing provider observations
- deterministic timeout/concurrency/rate-budget tests

## M4 — governed username and public-account discovery

**Status: complete**

- Sherlock 0.16.0 pinned as the username verifier
- reviewed eight-site allowlist
- killable child-process execution
- explicit positive/negative/unknown/illegal/WAF observations
- account hits are candidates, never identity claims
- no proxies, Tor/I2P, CAPTCHA/WAF bypass, browser opening, login/cookies or private-account access

## M5 — explainable evidence correlation engine

**Status: complete**

- deterministic correlation over stored evidence
- separate correlation run/factor records
- explicit contradiction/veto rules
- provenance-derived independence groups
- stale evidence remains visible and scores zero
- same-handle reuse alone remains insufficient evidence
- canonical digests and replay-safe persistence
- results remain `uncalibrated` and `is_identity_claim=false`
- no external calls, AI/ML or biometric matching in the identity decision path

## M6 — local evidence intelligence dashboard

**Status: complete**

- bounded typed case read model
- synthetic `/dashboard` operator view
- provenance, freshness, claims, candidates, factors, contradictions and stale evidence visible
- complete/no-evidence/empty/loading/error states
- PC/laptop keyboard/focus review
- Node 24 + lockfile + `npm ci` reproducible web toolchain

## M7 — private one-admin live research product

**Status: repository implementation complete**

Merged to `main` in private V1 merge commit
`bcadef6968dc20f17c8dd9dd1e9bec415b582c34`.

M7 now includes:

- one deployment-configured admin identity; no registration, teams, tenants or invitations;
- Argon2 password hashing with no plaintext credential in Git/browser code;
- opaque HttpOnly session cookie, bounded expiry, logout/revocation and CSRF protection;
- public root exposes synthetic/demo product content only and does not receive real case payloads;
- private `/admin` console for authenticated intake and research;
- same-origin Next.js `/api` proxy;
- reviewed Sherlock username discovery plus GitHub, GitLab and Codeforces public-profile enrichment;
- phone numbering-plan/carrier/region/time-zone metadata without subscriber-identity claims;
- exact public-email matching where a source explicitly exposes the address;
- bounded PDF/TXT/JPEG/PNG intake;
- structured retained research cases and private report rendering;
- Render deployment Blueprint with a public Next.js service and private FastAPI service.

Hosted acceptance remains an operational deployment gate rather than missing repository code. It requires the repository owner to connect Render, enter deployment secrets and verify the live boundary.

## M8 — privacy lifecycle, audit and source expansion

**Status: substantially incorporated into private V1**

Implemented:

- automatic expiry purge plus explicit per-case and delete-all workflows;
- audit events for login, research execution, case access and deletion without copying research seeds, provider payloads or session secrets;
- 30-day default retained-case lifecycle;
- persistent deployment disk with secrets outside Git;
- optional exact-match Brave public-web discovery for phone/email/handle/URL;
- bounded source/resource budgets and data-minimization rules;
- private API deployment so the research service has no public internet endpoint.

Post-deployment operational work remains:

- choose and document backup/restore policy after the real Render service exists;
- measure provider reliability, latency and cost before paid enrichment expands;
- review retention duration against actual operator use rather than assuming 30 days is optimal forever.

## M9 — evidence graph and report convergence

**Status: private V1 design implemented with one deliberate change**

The original roadmap proposed retaining a second persistent M1 graph for live research. That would duplicate personal data after a case was retained. Private V1 instead admits live provider evidence into an ephemeral canonical M1 graph, runs the existing deterministic M5 engine, and stores the resulting report/provenance decision record in the retained case.

Implemented:

- live provider outputs are normalized into canonical M1 evidence semantics for evaluation;
- M5 correlation runs over live account-candidate evidence;
- same-handle remains weak, exact-identifier overlap cannot self-bootstrap, stale/contradiction semantics remain explicit;
- converged reports include source observations, research pivots, M5 factors, gaps and provenance;
- deleting the retained case does not leave a hidden second persistent live-evidence database.

Export remains intentionally deferred until hosted retention/audit behavior has been exercised with operator-controlled data.

## Immediate next gate — hosted V1 acceptance

This is the next action before adding more providers or beginning calibration work:

1. connect the repository's `main` branch to one Render Blueprint;
2. confirm `personalattice-api` is created as a private service and has no public `onrender.com` endpoint;
3. enter `PERSONALATTICE_ADMIN_USERNAME` and `PERSONALATTICE_ADMIN_PASSWORD_HASH` as deployment secrets;
4. optionally enter `BRAVE_SEARCH_API_KEY` for licensed broad public-web discovery;
5. verify the unauthenticated public shell cannot read cases, audit records or research endpoints;
6. log in through the public web service and perform one self-audit using an operator-controlled identifier;
7. delete the test case, log out, and verify the same private endpoints return unauthorized again;
8. record the deployed URL, verification date and any production-only defects without committing private case data or credentials.

No further provider expansion should be merged before this gate passes. Production behavior is now the highest-value unknown.

## M10 — evaluation and calibration laboratory

**Status: next research milestone after hosted acceptance**

- consented/synthetic labelled evaluation datasets
- deterministic replay and factor-ablation studies
- false-positive/false-negative and threshold analysis
- no probability claim unless calibration evidence actually supports it

## Explicitly excluded from the current product

PersonaLattice does not add private-account bypass, credential/OTP theft, account-recovery probing, CAPTCHA/WAF evasion, covert subject contact, covert IP/device discovery or live tracking, hidden KYC acquisition, Internet-scale face identification, or regulated employment/housing/credit/insurance eligibility decisions.
