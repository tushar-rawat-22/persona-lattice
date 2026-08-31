# Live beta

PersonaLattice has passed its first software and real-host launch-candidate gate. The zero-secret public observer is now live, while the stable authenticated private beta remains the current deployment objective.

This document separates three things that are easy to confuse: the live public read-only product demo, a stable private beta, and a future multi-user SaaS deployment.

## What is ready now

The one-admin application has already been exercised as a production-shaped build on a real host. The accepted LC1 session covered authentication and CSRF, exact public-source research, retained cases, source-state and provenance display, M5's non-probabilistic evidence-strength presentation, reviewed document intake, restart persistence, backup/restore and Safari/Chrome acceptance.

The application can therefore be shown as a working product without waiting for every post-LC1 refinement or future source integration.

Do not describe it as a multi-user production SaaS. The current private runtime intentionally has one admin, one API worker, process-local sessions and SQLite case storage.

## Live zero-spend public product demo

The public observer is live at:

`https://persona-lattice.pages.dev`

It was created on 2026-08-31 from the canonical `tushar-rawat-22/persona-lattice` repository using the dedicated static public-demo build. Founder live smoke screenshots verified the overview and synthetic evidence workspace, including retained-case navigation, source states, correlation, observation timeline, evidence path, claims/open questions, operator-lifecycle simulation and loading/failure/coverage semantics.

The public demo is deliberately independent of the private research runtime. It contains fixed synthetic evidence and exposes the product's investigation hierarchy without provider execution, uploads, case mutation, retained private data or admin credentials. The `Private admin` path intentionally resolves to a public-safe boundary explanation; the Pages deployment does not provide an admin session.

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

The stable public URL is a separate deployment truth row from private-admin availability. A green static export or CI run alone is not sufficient evidence of the current live deployment. For future release claims, verify that the public URL is reachable and, where the hosting control plane exposes it, tie the deployed artifact to the exact repository commit before calling a new revision live.

## Temporary full-stack demonstration

A short-lived external full-stack demo may use a Cloudflare Quick Tunnel pointed at the local production-shaped web process. Use synthetic or otherwise safe demonstration cases only.

Cloudflare documents Quick Tunnels as testing/development infrastructure, with a random `trycloudflare.com` hostname and no production guarantee. A Quick Tunnel is suitable for temporary browser acceptance or a supervised demonstration, not a stable private-beta URL and not a place to depend on for retained evidence.

When the demo ends, stop the tunnel and local runtime.

## Stable private beta: preferred low-cost path

Now that the public observer is live, the primary deployment objective is the authenticated private workbench.

The lowest-churn private architecture is to keep the already-tested API, web process and SQLite database on a controlled host and publish the web process through a named Cloudflare Tunnel.

This requires a domain/zone that the operator controls. The public hostname maps through Cloudflare to the local web service; the API remains behind the same-origin `/api` proxy and does not need to be exposed directly.

This path preserves the current one-admin architecture and local persistent storage. The host must remain online whenever the private beta should be reachable, and host backups remain an operator responsibility.

A Cloudflare Tunnel does not remove PersonaLattice's own admin authentication requirement. The application still owns its session and CSRF boundary.

### Production-shaped host runner

`scripts/live_beta_start.sh` is the bounded local production runner for this path. It does not create a tunnel and never exposes the API itself.

The script:

- loads a separate owner-only production environment file (`0600` or `0400`);
- requires secure `__Host-` cookie configuration and an explicit persistent database path;
- runs the API launch preflight before starting services;
- builds and starts the production Next.js server rather than development mode;
- binds both API and web to loopback;
- runs exactly one Uvicorn worker;
- points the web server's `/api` proxy at the loopback API;
- leaves stable HTTPS ingress to the separately managed tunnel/host layer.

By default it reads:

```text
$HOME/.config/persona-lattice/production.env
```

Use `--preflight-only` to validate the production environment without starting the application processes.

The public tunnel/hostname should target only the loopback web port printed by the runner. Do not route the API port directly to the Internet.

## Hosted private alternative

The repository retains an optional Render topology at `deploy/render-paid.yaml`.

The API needs persistent storage because retained cases use SQLite. Render's default service filesystem is ephemeral, and persistent disk is not part of the zero-spend baseline. Do not deploy the current API on an ephemeral web service and then call retained cases durable.

The Render file remains an optional topology reference, not the current launch plan. Before using it, verify current pricing, storage and service limits in Render's own documentation.

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

## Private go-live gate

For a stable private beta, all of the following must be true on one exact release commit:

1. the deployment has a stable HTTPS endpoint;
2. the API is one worker/replica and the case database lives on persistent protected storage;
3. admin and provider configuration is supplied outside Git;
4. unauthenticated case and mutation requests fail closed;
5. login, logout, CSRF, one exact research case, retained-case reopen, restart persistence and backup/restore pass on the deployed environment;
6. browser checks confirm the current operator workspace renders correctly on Safari and Chrome;
7. the release SHA and rollback point are recorded in `docs/CONTINUITY.md`.

Post-LC1 UI improvements and future source additions can continue after that gate. They are not a reason to keep a working one-admin beta offline unless they expose a real correctness, privacy or security defect.

## Future SaaS gate

A real multi-user commercial service is a different architecture milestone. Before calling PersonaLattice that, move sessions to shared durable storage, move retained data to a production datastore designed for concurrent service instances, add account/tenant authorization boundaries, production observability and incident handling, governed backup/restore and deletion, and the required privacy/legal operating documents.

Do not hide that distinction in marketing. The current product is a serious private operator workbench with a live safe public demonstration surface and can be useful before it becomes a multi-tenant SaaS.
