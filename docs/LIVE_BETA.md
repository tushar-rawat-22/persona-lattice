# Live beta

PersonaLattice has a live zero-secret public observer and a protected one-admin private runtime under pre-external-operator acceptance. The public observer is not the private product, and the private product is not yet cleared for external operators.

This document separates three things that are easy to confuse: the live public read-only product demo, the current Mac-dependent private acceptance runtime, and a future multi-user SaaS deployment.

## What is ready now

The one-admin application has already been exercised as a production-shaped build on a real host, including authentication/CSRF, exact public-source research, retained cases, source-state and provenance display, non-probabilistic M5 evidence-strength presentation, reviewed document intake, persistence and browser acceptance slices.

Issue #340 is now the controlling external-operator gate. Tranche A is PARTIAL on exact private release `758b6ae3e96691e7f4880524e1ea49b826da0508`; external operator beta remains NO-GO until the bounded A → B → C acceptance sequence completes and no unresolved P0/P1 defect remains.

Do not describe the private runtime as an always-on service or a multi-user production SaaS. It intentionally has one admin, one API worker, process-local sessions and SQLite case storage, and it may be unavailable while the founder Mac sleeps.

## Live zero-spend public product demo

The public observer is live at:

`https://persona-lattice.pages.dev`

It was created from the canonical `tushar-rawat-22/persona-lattice` repository using the dedicated static public-demo build. It contains deterministic synthetic evidence and exposes the product's investigation hierarchy without provider execution, uploads, case mutation, retained private data or admin credentials. The `Private admin` path intentionally resolves to a public-safe boundary explanation; the Pages deployment does not provide an admin session.

`apps/web` has a dedicated static-export mode for this surface:

```bash
cd apps/web
npm ci --no-audit --no-fund
npm run test:public-demo
npm run build:public-demo
npm run test:public-demo-export
```

The output is `apps/web/out/`. The export includes the product overview, `/demo/`, an explicit `/operator-access/` boundary page and the static security/redirect policy used by Cloudflare Pages. In the Pages deployment, `/admin` and `/admin/*` redirect to `/operator-access/`; the normal private Next.js server does not interpret that Pages redirect file, so its authenticated `/admin` route remains unchanged.

The dedicated public build sets `PERSONALATTICE_PUBLIC_DEMO_ONLY=true`, clears `NEXT_PUBLIC_API_URL`, and removes the private operator route/bundle from the exported artifact. Never add credentials, a private API origin, login capability, provider execution or retained-case writes to this Pages deployment.

The Cloudflare Pages Git deployment contract is:

- repository: `tushar-rawat-22/persona-lattice`;
- production branch: `main`;
- root directory: `apps/web`;
- build command: `npm run build:public-demo`;
- output directory: `out`.

No provider key, admin password/hash, case database or private API URL belongs in the public Pages project. The build is intentionally useful with zero secrets and zero backend authority.

Cloudflare currently reports a successful PR/branch-preview Pages deployment for commit `758b6ae3e96691e7f4880524e1ea49b826da0508`. Because that check is PR-associated and reports preview URLs, it proves a successful Pages build/deployment for that commit in the preview context; it does **not** prove that the canonical production hostname is currently serving that SHA. A green static export, CI run or preview/control-plane check alone is not sufficient evidence for a fresh canonical-production or end-user reachability claim.

## Temporary full-stack demonstration

A short-lived external full-stack demo may use a Cloudflare Quick Tunnel pointed at the local production-shaped web process for supervised acceptance only. Use synthetic or otherwise safe demonstration cases.

Cloudflare Quick Tunnels are testing/development infrastructure with temporary hostnames and no production availability contract. They are not the stable private-beta product URL and must never be published as the public product link.

When the demonstration or acceptance session ends, stop the tunnel and local runtime.

## Current private acceptance runtime

The current private analyst runtime is deliberately Mac-dependent while zero-cash hosting constraints remain in force. It is acceptable for that runtime to be unavailable when the Mac sleeps; availability claims must say so plainly.

The exact release under Issue #340 Tranche-A acceptance is:

- private release: `758b6ae3e96691e7f4880524e1ea49b826da0508`;
- operational rollback: `8b773b4dc1560ab1160f1a3ce30705f6a4bae179`;
- runtime-manifest parent rollback: `4c0b05d4a0ae6215d8e1b884c78ef10f14432847`.

Reusable passed evidence, while inputs remain unchanged, includes API/web loopback isolation, persistent SQLite invariants, Safari authentication, retained safe-case reopen, Chrome login, Chrome 390/320px rendering and keyboard focus.

Remaining Tranche A work is MAC-DEPENDENT: complete and inspect one new bounded safe case; add an analyst decision and verify reload retention; search/reopen; synopsis/handoff; export/checksum review; logout denial/stale-UI behavior; restart, re-authenticate and prove case/decision/provenance persistence; authenticated Chrome journey; and the remaining Safari journey plus narrow viewport/keyboard checks.

Stop after Tranche A closes. Do not automatically begin Tranche B or Issue #222 source expansion.

## Deployment-contract lesson from #340-A

Tranche A exposed a P1 launchd preparation defect. PR #344 corrected it by invoking the Git-tracked 0644 runner through Bash and added regression coverage.

Future private-beta deployment preflight must explicitly verify executable-vs-interpreter invocation semantics for Git-tracked shell runners before live bootstrap. This is now a deployment-contract failure class and should not be rediscovered through production acceptance.

## Production-shaped host runner

`scripts/live_beta_start.sh` is the bounded local production runner. It does not create a tunnel and never exposes the API itself.

The script:

- loads a separate owner-only production environment file (`0600` or `0400`);
- requires secure `__Host-` cookie configuration and an explicit persistent database path;
- runs the API launch preflight before starting services;
- builds and starts the production Next.js server rather than development mode;
- binds both API and web to loopback;
- runs exactly one Uvicorn worker;
- points the web server's `/api` proxy at the loopback API;
- leaves HTTPS ingress to the separately managed tunnel/host layer.

By default it reads:

```text
$HOME/.config/persona-lattice/production.env
```

Use `--preflight-only` to validate the production environment without starting the application processes.

Any validation ingress should target only the loopback web port printed by the runner. Do not route the API port directly to the Internet.

## Hosted private alternative

The repository retains an optional Render topology at `deploy/render-paid.yaml`.

The API needs persistent storage because retained cases use SQLite. Render's default service filesystem is ephemeral, and persistent disk is not part of the zero-spend baseline. Do not deploy the current API on an ephemeral web service and then call retained cases durable.

The Render file remains an optional topology reference, not the current launch plan. Do not activate a billing-enabled or card-required service without explicit founder approval.

A future zero-cash persistent host is acceptable only if it truthfully preserves protected SQLite, exact release/rollback identity, loopback API isolation, restart persistence, backup/restore and stable HTTPS. Do not weaken any of those contracts simply to claim always-on availability.

## Required private deployment configuration

The minimum authenticated runtime needs server-side configuration for:

- `PERSONALATTICE_ADMIN_USERNAME`
- `PERSONALATTICE_ADMIN_PASSWORD_HASH`
- `PERSONALATTICE_DB_PATH`
- `PERSONALATTICE_COOKIE_SECURE=true` on HTTPS
- `PERSONALATTICE_SESSION_COOKIE=__Host-personalattice_session`

Generate the Argon2id admin hash locally with the repository helper. Never put the plaintext password, hash, case database, provider keys or research output in Git.

Optional sources may require their own server-side configuration. A missing optional credential or operator identity must disable/defer that provider before network contact; it must not make the rest of an investigation fabricate or silently omit results.

Current examples include:

- `BRAVE_SEARCH_API_KEY` for optional metered public-web discovery;
- `OPENALEX_API_KEY` for exact OpenAlex author lookup;
- `COMPANIES_HOUSE_API_KEY` for exact Companies House company lookup;
- `SEC_EDGAR_USER_AGENT` for SEC EDGAR automation identity. This is non-secret operator metadata, but it must contain a real maintainable application/operator identity and contact email.

## External-operator acceptance gate

Issue #340 is the release gate. External operator beta remains NO-GO until all of the following are proven on the controlled acceptance sequence:

1. one complete bounded case succeeds end to end;
2. one partial-provider-failure case remains useful and truthful;
3. one deliberate false-correlation case is rejected or flagged correctly;
4. retained create/reopen/decision/export/restart lifecycle passes;
5. auth/session/privacy negative matrix passes;
6. Chrome/Safari and narrow viewport acceptance passes;
7. exact release/rollback and recovery evidence are recorded;
8. no unresolved P0/P1 defect remains.

Acceptance is intentionally split into A → B → C. Tranche B must not begin automatically when A closes, and Issue #222 source expansion must not outrun #340 when a newly admitted source changes operator-visible behavior.

## Future SaaS gate

A real multi-user commercial service is a different architecture milestone. Before calling PersonaLattice that, move sessions to shared durable storage, move retained data to a production datastore designed for concurrent service instances, add account/tenant authorization boundaries, production observability and incident handling, governed backup/restore and deletion, and the required privacy/legal operating documents.

Do not hide that distinction in marketing. The current product is a serious private operator workbench with a live safe public demonstration surface, but external-operator readiness still depends on Issue #340 acceptance rather than feature count.
