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

- deterministic correlation over already-stored evidence
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

**Status: active**

M7 replaces the earlier multi-tenant plan. PersonaLattice currently has one operator, so access control is deliberately narrow and fail-closed rather than pretending to be a SaaS account system.

Implemented on the M7 branch:

- one deployment-configured admin identity; no registration, teams, tenants or invitations;
- Argon2id password hashing with no plaintext credential in Git/browser code;
- opaque HttpOnly session cookie, bounded expiry, logout/revocation and login throttling;
- browser bearer secret remains outside downstream authorization;
- independent per-session CSRF token required for unsafe authenticated requests;
- public root exposes synthetic/blurred product content only and does not receive real case payloads;
- private `/admin` console for authenticated intake and research;
- same-origin Next.js `/api` proxy for the private API;
- authenticated live username research through the governed Sherlock allowlist;
- allowlisted enrichment from GitHub's public user API while preserving same-handle-as-candidate semantics;
- phone numbering-plan/carrier/region/time-zone metadata without subscriber-identity claims;
- email/domain and public-URL normalization without invented ownership;
- retained private research cases in SQLite with configurable expiry, list/read/delete endpoints and UUIDs that do not bypass authentication;
- bounded PDF/TXT/JPEG/PNG intake; photo handling extracts file/EXIF metadata only and does not perform face identification;
- persistent-case and protected-write tests including known-UUID anonymous denial and CSRF failure cases.

Remaining M7 closure gates:

- final CI green after the image/EXIF block;
- add a concise structured human-readable case report instead of exposing only provider JSON;
- document the deployment constraint that in-memory sessions require one API worker;
- add deployment manifests using persistent protected storage and production-secure cookie settings;
- verify the hosted public preview returns no private case data before login;
- verify one real self-audit from an operator-controlled identifier before declaring M7 complete.

## M8 — privacy lifecycle, audit and source expansion

- automatic retention purge plus explicit delete-all workflow;
- audit events for login, research execution, case access and deletion without recording secrets;
- stronger at-rest deployment controls and backup policy;
- purpose/source policy records and data-minimization review;
- optional exact-match public-web search provider for phone/email/handle when a reviewed API credential is configured;
- provider reliability/cost tracking before paid enrichment expands;
- abuse controls remain relevant even for a single operator because the product can process third-party personal data.

## M9 — evidence graph and report convergence

- persist live provider outputs into the M1 Subject/Identifier/Observation graph rather than only the quick-case JSON store;
- run M5 explainable correlation over live retained evidence;
- render one consolidated evidence report with source timeline, connected identifiers, contradictions, freshness and unresolved gaps;
- generate export only after explicit retention/audit policy is in place.

## M10 — evaluation and calibration laboratory

- consented/synthetic labelled evaluation datasets
- deterministic replay and factor-ablation studies
- false-positive/false-negative and threshold analysis
- no probability claim unless calibration evidence actually supports it

## Explicitly excluded from the current product

PersonaLattice does not add private-account bypass, credential/OTP theft, account-recovery probing, CAPTCHA/WAF evasion, covert subject contact, covert IP/device discovery or live tracking, hidden KYC acquisition, Internet-scale face identification, or regulated employment/housing/credit/insurance eligibility decisions.
