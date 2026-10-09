# Roadmap

PersonaLattice is a private, evidence-first public-source research workbench. The public route is a synthetic/demo surface; real research, provider execution and retained cases belong to the authenticated operator workflow.

This file describes the current engineering sequence. Historical milestone detail belongs in Git history, closed issues and merged pull requests rather than accumulating here until the next session cannot tell what is still true.

## Permanent product rules

- Keep source observations, factual claims and correlation decisions separate.
- Preserve provenance for retained observations, admitted leads and triage results.
- Treat a discovered identifier as a research direction, not proof that records belong to the same person.
- M5 remains uncalibrated and non-probabilistic. It is evidence-strength triage, not identity probability.
- Keep production convergence bounded unless real labelled evaluation supports a change.
- No private-account bypass, credential/account-recovery probing, hidden KYC/government-ID acquisition, contact harvesting, covert personal/device IP discovery, live tracking, broad ownership traversal, reverse/bulk enumeration, biometric identity expansion or regulated eligibility decisioning.
- The required local operating baseline remains usable without paid enrichment, paid proxies or a paid database.
- External sources enter one at a time through current primary-source terms/privacy/auth/rate-limit/contact-risk review and the governed runtime path.

## Foundation — complete

The current one-admin product has the required evidence, provenance, normalization, provider governance, authentication, CSRF, reviewed-file intake, retained-case lifecycle, bounded convergence and deterministic M5 foundations.

`LAUNCH_CANDIDATE_1` was accepted on the candidate Mac on 2026-08-27. The exact host/browser-tested commit is `18b6b75b7dc28d3883752aec013911223726423c`; exact-commit post-merge CI run `33008932692` / CI #2226 passed.

The private LC1 evidence summary is outside Git at:

`$HOME/Library/Application Support/PersonaLattice/lc1/20260826T200923Z.json`

LC1 proved the software and real-host shape. It did not create a permanent public beta hostname.

## Current product baseline

PR #275 (`994cc50fb1f17a5dd6fde104179ed949e168b708`) is a historical operator-workspace milestone, not the current release. At the 2026-10-10 checkpoint, protected repository `main` is `1a70651a435e9263a1ed69b3c6125e20d6c11e4c`; verify it again before acting. Issue #340 accepted the bounded one-admin Mac-hosted private beta on release `af10d1c14615f439df46d050bb3850f001fb22d2` with rollback `a9a82e17e8a6edb0815374daac9edfccbb182ca5`. That acceptance is historical: it does not prove the private runtime is online now, that `main` is deployed privately, or that the product is ready for a public market.

Post-LC1 operator work has already delivered the major v2 workflow changes: compact application chrome, explicit decision synthesis, retained-case search/filter/sort, first-class provenance, decisive M5-factor summaries, source-execution truth, guarded deletion, stale-retention handling, explicit session expiry, loading/failure/empty-state distinctions, safe locator copy and narrow keyboard shortcuts for repeated case work.

Issue #252 remains the bounded operator-quality stream. Do not add UI changes simply because it is open. A change should remove a concrete analyst bottleneck, ambiguity or accessibility/interaction defect.

## Private beta — durable-host gate

The public observer is a static, synthetic, read-only Cloudflare Pages export. It is not the authenticated private product. The accepted Mac-hosted private beta is a bounded operator-validation milestone, not an always-on service. Issue #324 remains open until a real durable host passes acceptance. Do not claim always-on availability or market readiness based on green CI, the public observer, or a past Mac acceptance.

Before activating a private host, close regression-backed session-expiry concealment, failed-logout revocation and Linux release/recovery risks, including retained prepared-release preservation and enabled-versus-running service-state restoration. Treat these as source/synthetic risk findings, not established live incidents. Validate the Evidence Decision Desk at 1440/390/320 widths with keyboard/focus/reduced-motion and degraded, no-match, review-gated, auth-expired and destructive-action states. Do not substitute synthetic checks for closed real-user validation.

The durable-host acceptance gate is operational:

1. choose a stable HTTPS operating path;
2. provide persistent protected storage for SQLite;
3. supply admin/provider configuration outside Git;
4. deploy one API worker/replica;
5. rerun the bounded auth/CSRF/research/persistence/backup/browser smoke on the exact release SHA;
6. record release and rollback evidence in `docs/CONTINUITY.md`.

`docs/LIVE_BETA.md` is authoritative for the current choices. A controlled persistent host behind a named Cloudflare Tunnel is a possible future architecture only if a lawful, genuinely zero-cash stable hostname/zone and provider capacity are available. A card solely for identity verification requires explicit founder approval after disclosure of any temporary authorization hold. No paid activation or domain purchase is authorized. The repository retains an optional paid Render reference at `deploy/render-paid.yaml`, not a current spending plan.

Do not call a random Quick Tunnel a permanent beta endpoint, and do not place the current SQLite case store on an ephemeral hosted filesystem.

## Source expansion

Issue #222 governs source discovery/admission. The pre-LC1 freeze is over; source expansion resumed after LC1 under the existing one-source-per-PR discipline.

Prefer exact official APIs, registries and standards with strong provenance and sustainable zero-direct-cost operation. Reject/defer candidates when commercial/privacy terms, response shape, operational limits or matching semantics do not fit even if the endpoint is technically free.

Recent post-LC1 source work includes:

- GLEIF exact LEI legal-entity evidence, merged in PR #245;
- SEC EDGAR exact-CIK submissions metadata, governed through the shared runtime and Quick Research by PR #254.

Both remain deliberately exact/bounded, emit no recursive leads and keep `identity_claim=false`.

Do not expand them into company/person fuzzy search, address/contact enrichment, filing-body ingestion, ownership traversal, reverse lookup or bulk enumeration.

For detailed source status, read Issue #222, `docs/SOURCE_ADMISSION_QUEUE.md` and the source-specific admission files. Do not duplicate the entire provider catalog in this roadmap.

## Evaluation

Real labelled/consented evaluation remains the gate for changing graph depth, M5 semantics or making population-performance claims.

Synthetic regression cohorts can detect implementation regressions but do not justify claims about false-positive rate, false-negative rate, identity probability, calibration or population accuracy.

If genuine reviewed/consented M10 evidence becomes available, evaluate it before changing the production correlation/convergence policy.

## After durable private-host acceptance

Durable private-host acceptance does not authorize commercial or broad-market launch. That separate gate requires evidence for product correctness; reliability and scalability on a real host; security, privacy and authority boundaries; data integrity and recovery; frontend accessibility and UX; observability and rollback; closed real-user validation; and commercial/legal readiness, with no unresolved launch-blocking defects.

Continue in this order unless a real defect changes the priority:

1. close concrete operator-workspace defects that materially slow case work;
2. admit high-value exact/provenance-rich zero-direct-cost sources one at a time;
3. improve deployment/operations based on actual beta use;
4. collect legitimate evaluation evidence;
5. only then consider multi-user SaaS architecture.

A multi-user service will require shared durable sessions, tenant-aware authorization, a concurrent production datastore, governed backups/deletion, observability/incident handling and privacy/legal operating documentation. Do not bolt multiple workers/users onto the current process-local session + SQLite architecture and call it scaling.

## Change discipline

A new engineering block must improve at least one of: defensible source coverage, real evaluation, correctness, security/privacy, release operations or a concrete investigator task.

For implementation PRs:

- keep the change bounded;
- do not weaken a regression to make CI green;
- merge only after exact unchanged-head CI is fully green and review blockers are resolved;
- use an expected-head merge guard;
- after merge, start the next defensible increment rather than manufacturing status churn.

For session handover and exact current state, use `docs/CONTINUITY.md`.