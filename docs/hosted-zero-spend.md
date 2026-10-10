# Zero-spend hosted architecture

PersonaLattice has two deliberately different deployment classes.

The **public observer** is the canonical always-on public link. It is a static Cloudflare Pages export containing synthetic fixtures only. It must not depend on the founder Mac, run providers, accept uploads, expose retained cases, or contain a private API origin or credential.

The **private beta** is a one-admin authenticated evidence workspace with persistent SQLite. The current Mac/ngrok deployment is validation infrastructure: it is allowed to be offline while the Mac sleeps and must never be marketed as an always-on service.

Private always-on hosting is **not yet established**.

## Zero-cash rule

Current infrastructure decisions must cost ₹0. Do not activate:

- a purchased domain;
- paid database, storage or usage-billed hosting;
- Pay As You Go, billing upgrades or resources that can incur charges without explicit founder approval.

Issue #324 permits *proposing* a genuinely zero-cash free-tier signup that requires a card solely for identity verification. This is not approval to sign up: the founder must personally approve the card/identity step after any temporary authorization hold, billing terms and limits are disclosed. Never collect card details in Git or the operator runtime.

A provider's marketing label of “free tier” or “always free” is not sufficient. Account requirements, billing activation, persistent-storage guarantees and current terms all matter.

Free stateless web hosts are not acceptable for the retained private-beta database when their local filesystem is ephemeral or disappears during spin-down/redeploy. Persistence and recovery are product requirements, not optional hosting details.

If no genuinely zero-cash host satisfies the stateful private-beta contract, keep the private beta local rather than weakening persistence or security.

## Provider-neutral Linux bundle

`deploy/linux/` prepares the current one-admin architecture for a small persistent Linux host later without changing application authority:

- an exact-SHA release checkout under `/opt/persona-lattice/releases/`;
- a dedicated `personalattice` system user;
- root-owned configuration at `/etc/persona-lattice/production.env`, readable but not writable by the dedicated service group;
- persistent SQLite under `/var/lib/persona-lattice/data/`;
- release-specific prepared runtime state under `/var/lib/persona-lattice/runtime/<sha>/`;
- a systemd service with restart-on-failure and process hardening;
- web bound only to `127.0.0.1:13000`;
- API bound only to `127.0.0.1:18000` and reachable externally only through the web `/api` proxy;
- SQLite integrity-checked backup/restore contracts through Linux wrappers;
- a host verifier that checks release identity, service health, same-origin API health and loopback-only listeners;
- an optional Cloudflare Tunnel configuration that publishes the web port only.

Preparation is release-addressed. `sudo bash deploy/linux/prepare-release.sh <current-main-full-sha>` clones and builds only the freshly resolved canonical `main`, seals the release tree to root ownership, rejects broken or escaping symlinks, and switches `/opt/persona-lattice/current` only after the service becomes healthy. A failed activation restores the prior release and unit and verifies their health.

Rollback does not fetch, build or execute preparation code from a historical checkout. Select an already prepared retained release with `sudo bash deploy/linux/select-prepared-release.sh <retained-full-sha>`. The selector accepts only an immutable root-owned SHA directory directly below `/opt/persona-lattice/releases`, permits symlinks only when they resolve inside that exact release, verifies that the installed systemd unit still matches the current release, and restores the prior selection if the requested release fails health checks. The runtime user never owns the production environment file or a sealed release tree.

The environment template contains placeholders only. A real password hash, provider key, tunnel token or tunnel credential file must never be committed.

## Provider status under the current policy

Oracle documents Always Free compute and persistent block storage. OCI is a **conditional candidate**, not an accepted host: signup requires identity verification with a valid card and may place a temporary authorization hold; free-tier capacity is not guaranteed and there is no free-tier SLA. Issue #324 allows proposing this option, not activating it without founder approval. Do not request signup until a bounded, immediately usable deployment and recovery plan has passed review.

Deplexo is **not a private-runtime candidate**: its terms dated 2026-10-05 prohibit private/password-protected services, including on free plans.

The Linux bundle stays provider-neutral. No provider research authorizes weakening SQLite persistence, loopback API isolation, authentication, recovery or exact release identity. No paid-account upgrade is approved to work around free-capacity limits.

Primary provider evidence checked on 2026-10-09:

- Oracle Always Free resources: https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm
- Oracle Free Tier FAQ/account requirements, authorization holds, capacity and SLA: https://www.oracle.com/cloud/free/faq/
- Deplexo terms (2026-10-05): https://deplexo.com/terms
- Cloudflare Tunnel Linux service: https://developers.cloudflare.com/tunnel/advanced/local-management/as-a-service/linux/
- Cloudflare Tunnel architecture: https://developers.cloudflare.com/tunnel/

Provider terms can change. Re-check primary documentation before any future activation decision.

## Cloudflare ingress option

Cloudflare Tunnel can connect outward from a future Linux host, so PersonaLattice application ports do not need public inbound firewall rules. `deploy/linux/cloudflared-config.yml.example` intentionally routes only `127.0.0.1:13000` and terminates unmatched ingress with HTTP 404. Port `18000` must never be a tunnel route.

A stable tunnel hostname can require a Cloudflare-managed hostname/zone. Do not purchase a domain under the current zero-cash policy merely to make the private beta look polished. If a genuinely zero-cash stable hostname is not already available, keep the current private-beta validation arrangement. Cloudflare Quick Tunnels remain suitable for short-lived testing only, not as the stable private-beta target.

Cloudflare ingress, if used later, is an additional network layer rather than a replacement for PersonaLattice admin authentication. The application must retain its own session and CSRF boundary.

## Backup posture

SQLite remains the correct store while the product is one-admin and measured concurrency, tenancy or HA requirements do not justify a database migration. The existing backup process creates an integrity-checked SQLite backup plus SHA-256 and release provenance, then performs a restore check before declaring success.

An off-host S3-compatible adapter may be prepared without activation, but an off-host target must not be enabled unless it has a genuinely zero-cash durable path with any required identity verification separately approved. Until then, keep verified owner-only local backups and do not treat an ephemeral free filesystem as disaster recovery.

## Future host activation gate

Do not activate a private always-on host under the current policy unless all of these are true:

1. Current official provider terms confirm zero-cash operation without paid billing activation. Any card solely for identity verification requires explicit founder approval and prior disclosure of possible authorization holds.
2. Persistent storage is genuinely durable across restart/redeploy and does not silently expire under the free plan.
3. The host supports the existing one-worker architecture and protected SQLite path.
4. Exact release identity and rollback remain verifiable.
5. Web and API can stay loopback-only behind a controlled HTTPS ingress boundary.
6. Owner-only secrets remain outside Git.
7. Integrity-checked backup/restore is available before ingress changes.
8. The changed-host acceptance surface can cover anonymous denial, admin login/logout, secure cookie/CSRF mutation, one retained-case reopen, persistence across service restart, release identity, browser quick smoke and API loopback-only.

If any of those fail, the correct action is to remain on the Mac validation beta. Do not trade away persistence or security merely to obtain an “always-on” label.

A commercial multi-user launch is a separate NO-GO milestone until product correctness, real-host reliability/scalability, security/privacy, data recovery, UX/accessibility, observability/rollback, closed human validation and commercial readiness have been evidenced. Team authorization, HA, stronger off-host backup, operational monitoring and a database migration should be justified by measured demand rather than installed pre-emptively.
