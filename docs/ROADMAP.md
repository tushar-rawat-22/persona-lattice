# Roadmap

PersonaLattice is a private, evidence-first research workbench. The public route is a demo surface; real intake, provider execution and retained case data belong to one authenticated operator account unless a future security/privacy review changes that model.

## Permanent product rules

- Observations, factual Claims and correlation results remain separate.
- Every lead and conclusion keeps provenance.
- A lead is a research direction, not proof of identity.
- Same-handle reuse alone remains insufficient evidence.
- M5 remains uncalibrated evidence-strength triage, not identity probability.
- Contradictions, vetoes and stale evidence remain visible.
- No AI/ML/embedding/biometric identity decision is authorized by the current roadmap.
- No private-account bypass, credential/account-recovery enumeration, hidden KYC/government-ID acquisition, covert personal/device IP discovery, live tracking or regulated eligibility decisioning is a product capability.
- The default product must remain usable without paid APIs, paid hosting, paid databases, paid proxies or paid enrichment.

## M0-M6 — core platform

**Status: complete**

Repository/CI, evidence and provenance storage, normalization, bounded file intake, the governed provider framework, reviewed Sherlock discovery, deterministic M5 correlation and the local evidence dashboard are implemented.

M5 permanent outputs remain `calibration_status=uncalibrated` and `is_identity_claim=false`.

## M7 — private one-admin research product

**Status: implemented and manually accepted locally**

The private product has one deployment-configured admin, Argon2 password verification, HttpOnly sessions, CSRF protection, a private `/admin` route, same-origin API proxying, retained cases, delete/expiry controls and live bounded research.

Current live research sources include reviewed Sherlock, GitHub, GitLab, Codeforces, Bluesky public profiles for valid AT handles, phone numbering-plan metadata and public DNS infrastructure metadata. Brave exact public-web search is optional when configured.

Local operation is the zero-spend baseline. Paid hosting is optional; the previously reviewed Render topology is retained only at `deploy/render-paid.yaml`.

## M8 — privacy lifecycle and operations

**Status: substantially implemented**

Implemented: 30-day default retained-case lifecycle, automatic expiry purge, explicit deletion, privacy-safe audit events, secrets outside Git, and bounded request/concurrency/timeout/response limits.

Backup/restore design remains deferred until a persistent hosted production store is actually selected.

## M9 — evidence graph and convergence

**Status: implemented**

Private V1 admits live provider observations into an ephemeral canonical M1 graph, runs M5 and retains bounded report/provenance records. It does not create a second persistent raw-personal-data graph.

### V2-A — typed recursive evidence lead graph

**Status: complete — PR #20**

Exact-field lead extraction, typed lead kinds/dispositions, M1-consistent normalization and fail-closed handling for sensitive field classes.

### V2-B — deterministic frontier orchestration

**Status: complete — PR #21**

Reservation-safe scheduling, duplicate/cycle suppression, reason-coded outcomes and additive lead-graph report state.

Production limits remain **depth 2 / 12 nodes**. Raising them requires evaluation evidence.

### V2-C — source capability registry and planner

**Status: complete — PR #22**

Capability, execution authority, lifecycle state, cost class, credential class, source-policy review and recursive eligibility are explicit. Planned sources remain non-executable by construction.

### V2-D — runtime consistency and architecture closure

**Status: complete — PRs #89-#90**

Every executable network source is behind the governed runtime. The executable legacy-network allowance is empty. Catalog, binding, provider registry and process runtime ownership are checked symmetrically. Required active recursive sources must remain zero-spend eligible; non-zero-spend recursive sources can only be optional.

Source-run accounting is phase-proven, retained evidence/provenance has canonical owners, historical retained formats remain read-only compatible, and the reviewed-document chain is server-owned from extraction through explicit case execution.

The default operating contract is `docs/ZERO_SPEND_RUNBOOK.md`; paid Render deployment is an optional reference at `deploy/render-paid.yaml`.

## M10 — evaluation and calibration laboratory

**Status: deterministic replay and consented-analysis infrastructure established; representative evaluation remains**

Established:

- complete deterministic source-state/failure fixture coverage;
- provider attempt/failure/no-match/yield counters with explicit denominators;
- graph growth, depth, duplicate and budget-stop counters;
- label-gated wrong-pivot measurement;
- controlled graph-limit comparison through the production `LeadFrontier`;
- a six-fixture synthetic cohort spanning username, email, URL and reviewed-phone seeds;
- provider-boundary request-cost and observation-yield accounting;
- versioned replay fingerprints for exact cohort inputs and deterministic results;
- replay-anchored M5 factor-ablation manifests and real-engine omission execution;
- rollback-only diagnostic M5 execution so M10 experiments do not become retained evidence;
- UUID-independent semantic fixture/result fingerprints;
- explicit synthetic-vs-consented label-provenance manifests;
- consented-only scenario accounting with exact numerator/denominator counts rather than unsupported population error-rate claims.

### Current controlled graph result

The current depth-2 / 12-node synthetic policy admits 9 labelled pivots: **8 relevant and 1 wrong**. It performs 11 simulated source attempts: 9 yield-producing attempts and 2 provider failures, for 11 abstract request-cost units and 9 observation-yield units.

A depth-3 / 12-node candidate admits three additional labelled pivots. In these fixtures, **all three are wrong-labelled and no additional relevant pivot is gained**. It adds 3 simulated attempts, 3 request-cost units and 3 observation-yield units.

This is diagnostic synthetic evidence, not population evidence or monetary cost. Production recursion stays depth 2 / 12 nodes.

### Current controlled M5 ablation result

- compatible profile metadata omission: `possible_match` 35 → `insufficient_evidence` 20;
- exact confirmed identifier omission: `strong_candidate` 75 → `insufficient_evidence` 20;
- independent cross-link omission: `strong_candidate` 70 → `possible_match` 35;
- diagnostic hard-contradiction omission: `contradicted` 0 → `strong_candidate` 90.

The contradiction omission is safety-critical diagnostic work only. No production factor weight, threshold, veto or calibration semantic changed.

### Remaining M10 gate

The bottleneck is real label evidence, not another synthetic metric. Assemble a genuinely consented or independently reviewed cohort whose external evidence records satisfy the existing provenance contract, then run it through the consented-only accounting boundary. Do not relabel regression fixtures as consented to manufacture progress, and do not publish false-positive/false-negative or probability terminology until cohort design and denominators genuinely support it.

## Reviewed source expansion

V2-D is closed. New sources must use the existing catalog → binding → provider registry → process-wide `ProviderRuntime` → typed source-run → canonical evidence path.

### Bluesky public profiles

**Status: active — PR #98**

Bluesky is credentialless and zero-direct-cost. Only normalized values that pass the AT-handle admission contract can trigger a request. Plain usernames and malformed/`@` UI forms are skipped before provider execution.

Retained fields stay minimal: DID, normalized handle and optional display name plus account-candidate/non-identity/public-visibility flags. Public-web opt-out and suspended/deactivated accounts are neutral attempted `withheld` outcomes rather than `not_found` or provider failure.

### Gravatar

**Status: planned — admission preflight complete in PR #113**

The provider-specific email-hash and returned-profile validation contract exists, but activation remains blocked by the provider-terms/privacy-policy requirement. A future activation also needs a free server-side key outside Git and deterministic provider fixtures. Gravatar must remain unnecessary to the zero-spend baseline.

### WebFinger public-link resolution

**Status: planned — parser, transport, URL-only semantics and exact-host policy gate complete in PRs #115, #117, #119 and #121**

The historical source key remains `webfinger_activitypub` for compatibility, but its reviewed meaning is WebFinger URL → URL public-link resolution only. ActivityPub actor fetching is a separate future capability and remains unapproved.

The pre-activation stack has four independent controls:

1. explicit HTTPS profile-URL/JRD admission;
2. fresh-DNS, globally-routable, IP-pinned HTTPS transport with bounded HTTPS-only redirects;
3. URL-only source semantics with no generic username/name emission;
4. time-bounded **exact-host** source-policy approval with no wildcard or subdomain inheritance.

A concrete `mastodon.social` review did not establish a sufficiently explicit current host-specific terms/privacy basis for approval. The gate was not weakened; the production exact-host registry remains empty. WebFinger stays non-executable until a concrete host passes that policy.

### RDAP

**Status: planned — admission PR #123; metadata-only contract PR #126; authoritative transport PR #128; bounded bootstrap cache PR #130**

RDAP is being reviewed as zero-spend domain registration metadata from authoritative services. The source contract remains metadata-only: `rdap_domain_registry.emits = frozenset()`. Registrant/registrar/contact names, organizations, addresses, email addresses and telephone numbers are excluded from the admitted observation and cannot become typed subject leads.

PR #128 corrected IANA bootstrap authority selection to RFC 9224 longest matching DNS-suffix semantics and added the pre-activation network boundary: fresh DNS/global-address validation before every hop, IP-pinned HTTPS with hostname TLS validation, bounded HTTPS redirects, four-second connection timeout, 64 KiB response ceiling, RDAP media-type validation, explicit 404/429/transient/malformed handling, and fallback to an equivalent bootstrap service only after transient unavailability.

PR #130 adds one process-wide owner for IANA's fixed `https://data.iana.org/rdap/dns.json` registry. Fresh snapshots are reused without network I/O; expired snapshots refresh conditionally with ETag/Last-Modified when available; HTTP freshness information drives TTL with bounded fallback/cap; `no-store` is not retained; concurrent refresh is serialized; malformed/oversized/unexpected redirects fail closed; and an expired snapshot is not silently served after refresh failure. The cache holds public routing metadata only and requires no credential or paid service.

A redirect or rebinding failure found **after** an RDAP provider has already responded remains post-contact result validation, not a no-attempt policy failure. The transport preserves the bootstrap-derived query URL and final response URL separately for later exact provenance handling.

RDAP remains `PLANNED`, unbound, source-policy-unreviewed and non-recursive until the final atomic activation is reviewed. Redaction and missing fields remain authoritative. No WHOIS fallback, RDRS/nonpublic-data workflow, bulk/reverse lookup or contact harvesting is approved.

## Immediate next gate

Do not reopen V2-D architecture casually, remove safety-critical M5 vetoes because an ablation changes the score, or raise recursion because a fixture family looks favorable.

For evaluation, prioritize genuinely consented/reviewed label evidence.

For source expansion, complete **one atomic governed RDAP activation** through catalog → binding → provider registry → shared runtime → typed source-state → canonical observation. Activation must preserve metadata-only output, redaction authority, deterministic success/not-found/malformed/rate-limit/unavailable fixtures, and the zero-spend baseline. WebFinger remains planned unless a concrete host passes the existing exact-host source-policy gate. Gravatar remains blocked on its privacy-policy requirement. ActivityPub actor fetching remains unapproved.

Production recursion remains **depth 2 / 12 nodes**. M5 remains uncalibrated evidence-strength triage and `hard_contradiction` remains a production veto.

Success means the operator can answer for every hop:

> What source produced this clue, why was it allowed to become a lead, what did the system do with it, and what remains unknown?
