# Roadmap

PersonaLattice is a private, evidence-first public-source research workbench. The public route is a synthetic/read-only observer; real research, provider execution and retained cases belong to the authenticated operator workflow.

This file describes the current engineering sequence. Historical milestone detail belongs in Git history, closed issues and merged pull requests rather than accumulating here until the next session cannot tell what is still true.

For the exact current release checkpoint, read `docs/CURRENT_RELEASE_STATUS.md` and verify it against fresh GitHub/provider evidence before acting.

## Permanent product rules

- Keep source observations, factual claims and correlation decisions separate.
- Preserve provenance for retained observations, admitted leads and triage results.
- Treat a discovered identifier as a research direction, not proof that records belong to the same person.
- M5 remains uncalibrated and non-probabilistic. It is evidence-strength triage, not identity probability.
- Keep production convergence bounded unless real labelled evaluation supports a change.
- No private-account bypass, credential/account-recovery probing, hidden KYC/government-ID acquisition, contact harvesting, covert personal/device IP discovery, live tracking, broad ownership traversal, reverse/bulk enumeration, biometric identity expansion or regulated eligibility decisioning.
- The required local operating baseline remains usable without paid enrichment, paid proxies or a paid database.
- External sources enter one at a time through current primary-source terms/privacy/auth/rate-limit/contact-risk review and the governed runtime path.
- Provider failure never becomes identity evidence.

## Foundation — complete

`LAUNCH_CANDIDATE_1` proved the one-admin software and real-host shape. Subsequent operator, retained-case, deployment and public-observer work has materially advanced the product beyond that checkpoint.

The current architecture still intentionally uses one authenticated admin, one API worker and persistent SQLite for the private operator runtime. That is a valid private-beta shape, not a multi-user SaaS architecture.

The public observer at `https://persona-lattice.pages.dev` is a separate static Cloudflare Pages surface. It must remain synthetic, sanitized, read-only, Mac-independent and free of private authority/data.

## Current company gate — Issue #340

The active company gate is Issue #340: comprehensive pre-external-operator acceptance. External operator beta remains **NO-GO** until that issue's required evidence is complete and no unresolved P0/P1 remains.

Visual differentiation from #339/#341 is complete. Do not reopen broad UI polishing without an evidenced operator defect.

Acceptance is intentionally sequenced in bounded tranches **A → B → C**. Do not start a later tranche merely because its tests are convenient to run.

### Tranche A — PARTIAL

Exact private release under acceptance:

`758b6ae3e96691e7f4880524e1ea49b826da0508`

Operational rollback:

`8b773b4dc1560ab1160f1a3ce30705f6a4bae179`

Runtime-manifest parent rollback:

`4c0b05d4a0ae6215d8e1b884c78ef10f14432847`

Reusable passed evidence, while inputs remain unchanged:

- API/web loopback-only boundary;
- persistent SQLite invariants;
- Safari authentication;
- retained safe-case reopen;
- Chrome login;
- Chrome 390px and 320px viewport acceptance;
- Chrome keyboard-focus acceptance.

Remaining Tranche A work is the protected local/browser lifecycle only:

1. complete and inspect one new bounded safe case;
2. add an analyst decision and prove reload retention;
3. search and reopen the case;
4. inspect synopsis/handoff;
5. review export and checksum;
6. verify logout denial and stale-UI handling;
7. restart, re-authenticate and prove case/decision/provenance persistence;
8. complete the authenticated Chrome journey;
9. complete the remaining Safari journey plus narrow viewport/keyboard checks.

These remaining steps are **MAC-DEPENDENT**. Cloud-side work may continue only when it does not change the release under acceptance or jump ahead to Tranche B.

PR #344 fixed a P1 deployment-contract defect discovered during Tranche A: the Git-tracked `0644` private-beta preparation runner must be invoked explicitly through Bash. Treat executable-vs-interpreter invocation semantics as a deployment-preflight contract and keep the regression.

### Tranche B — after A closes

Exercise degraded-source and evidence-integrity attacks: no-match, blocked, rate-limit, timeout, malformed response, partial outage, all-unavailable, stale/duplicate/conflicting evidence, weak-vs-strong correlation and deliberate false-correlation/M5 semantics.

A provider outage, block, timeout or malformed response must remain source-state truth and must contribute no fabricated identity evidence.

### Tranche C — after B closes

Complete the remaining destructive/recovery/session/browser matrix and final external-operator GO/NO-GO evidence, including exact release/rollback/recovery truth and no unresolved P0/P1.

## Source expansion

Issue #222 governs source discovery/admission. It remains valuable, but **must not outrun Issue #340 when a source changes operator-visible behavior or evidence semantics**.

Prefer exact official APIs, registries and standards with strong provenance and sustainable zero-direct-cost operation. Reject/defer candidates when commercial/privacy terms, response shape, operational limits or matching semantics do not fit even if the endpoint is technically free.

Source work remains one source per PR after the acceptance sequence permits it. Do not broaden exact providers into fuzzy person search, address/contact enrichment, filing-body ingestion, ownership traversal, reverse lookup or bulk enumeration merely because an upstream interface supports it.

For detailed source status, read Issue #222, `docs/SOURCE_ADMISSION_QUEUE.md` and the source-specific admission files. Do not duplicate the entire provider catalog in this roadmap.

## Availability and hosting

Public observer availability and private operator availability are separate truths.

- Public observer: static Cloudflare Pages, synthetic/read-only, Mac-independent.
- Private analyst runtime: currently protected and **MAC-DEPENDENT**; it is validation infrastructure, not truthful 24/7 hosting.
- Private always-on hosting: not established.

Do not publish ngrok, localhost or Cloudflare Quick Tunnel hostnames as product links. Do not weaken persistent SQLite, authentication, API isolation, restart persistence, backup/restore, release identity or HTTPS simply to claim always-on availability.

Zero cash remains the infrastructure constraint. Do not activate paid or billing-enabled infrastructure without explicit founder approval.

## Evaluation

Real labelled/consented evaluation remains the gate for changing graph depth, M5 semantics or making population-performance claims.

Synthetic regression cohorts can detect implementation regressions but do not justify claims about false-positive rate, false-negative rate, identity probability, calibration or population accuracy.

If genuine reviewed/consented M10 evidence becomes available, evaluate it before changing the production correlation/convergence policy.

## After #340 closes

Continue in this order unless a real defect changes the priority:

1. act on any acceptance defect/regression discovered by #340;
2. admit high-value exact/provenance-rich zero-direct-cost sources one at a time under #222;
3. improve deployment/operations based on actual beta use;
4. collect legitimate evaluation evidence;
5. only then consider multi-user SaaS architecture.

A multi-user service will require shared durable sessions, tenant-aware authorization, a concurrent production datastore, governed backups/deletion, observability/incident handling and privacy/legal operating documentation. Do not bolt multiple workers/users onto the current process-local session + SQLite architecture and call it scaling.

## Change discipline

A new engineering block must improve at least one of: defensible source coverage, real evaluation, correctness, security/privacy, release operations or a concrete investigator task.

For implementation PRs:

- keep the change bounded;
- compare do-nothing, the smallest reversible change and a larger change before choosing;
- do not weaken a regression to make CI green;
- merge only after exact unchanged-head CI is fully green and review blockers are resolved;
- use an expected-head merge guard;
- convert genuine runtime/browser/CI failures into the smallest regression/eval and classify the root cause;
- reuse passed evidence when relevant inputs are unchanged;
- after merge, start the next defensible increment rather than manufacturing status churn.

For session handover and exact current state, use `docs/CURRENT_RELEASE_STATUS.md` and `docs/CONTINUITY.md`, then verify them against fresh GitHub/provider evidence.