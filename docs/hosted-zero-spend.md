# Zero-spend hosted architecture

PersonaLattice has two deliberately different deployment classes.

The **public observer** is the canonical always-on public link. It is a static Cloudflare Pages export containing synthetic fixtures only. It must not depend on the founder Mac, run providers, accept uploads, expose retained cases, or contain a private API origin or credential.

The **private beta** is a one-admin authenticated evidence workspace with persistent SQLite. The current Mac/ngrok deployment is validation infrastructure: it is allowed to be offline while the Mac sleeps and must never be marketed as an always-on service.

Private always-on hosting is **not yet established**.

## Zero-cash rule

Current infrastructure decisions must cost ₹0 and must not require a billing-enabled account or card-backed signup. Do not require:

- a purchased domain;
- paid database or storage;
- paid or usage-billed hosting;
- a credit/debit card for provider activation;
- an account that can incur charges without an explicit founder policy change.

A provider's marketing label of “free tier” or “always free” is not sufficient. Account requirements, billing activation, persistent-storage guarantees and current terms all matter.

Free stateless web hosts are not acceptable for the retained private-beta database when their local filesystem is ephemeral or disappears during spin-down/redeploy. Persistence and recovery are product requirements, not optional hosting details.

If no truly no-card, hard-free host satisfies the stateful private-beta contract, keep the private beta local rather than weakening persistence or security.

## Provider-neutral Linux bundle

`deploy/linux/` prepares the current one-admin architecture for a small persistent Linux host later without changing application authority:

- an exact-SHA release checkout under `/opt/persona-lattice/releases/`;
- a dedicated `personalattice` system user;
- owner-only configuration at `/etc/persona-lattice/production.env`;
- persistent SQLite under `/var/lib/persona-lattice/data/`;
- release-specific prepared runtime state under `/var/lib/persona-lattice/runtime/<sha>/`;
- a systemd service with restart-on-failure and process hardening;
- web bound only to `127.0.0.1:13000`;
- API bound only to `127.0.0.1:18000` and reachable externally only through the web `/api` proxy;
- SQLite integrity-checked backup/restore contracts through Linux wrappers;
- a host verifier that checks release identity, service health, same-origin API health and loopback-only listeners;
- an optional Cloudflare Tunnel configuration that publishes the web port only.

Preparation is release-addressed. `prepare-release.sh <full-sha>` builds a release before switching `/opt/persona-lattice/current`; the same command with a previously accepted SHA is the rollback mechanism. The runtime user does not own the prepared source tree after preparation.

The environment template contains placeholders only. A real password hash, provider key, tunnel token or tunnel credential file must never be committed.

## Provider status under the current policy

Do not ask the founder to create an OCI account now.

Oracle still documents Always Free compute and persistent block storage, so OCI remains a technically relevant **future** Linux-host candidate. But Oracle's current Free Tier signup documentation requires valid credit/debit-card information and may use temporary authorization holds. That conflicts with the current no-card/no-billing-activation policy.

Therefore:

- OCI is not a current blocker;
- OCI signup is not a current action;
- the Linux bundle must remain provider-neutral;
- any alternative provider with card or billing activation requirements is held under the same rule;
- provider capacity or signup research does not justify weakening SQLite persistence, loopback API isolation, authentication, recovery or release identity.

If the founder later changes the no-card/no-billing policy, re-check Oracle's official account, billing, free-tier and capacity documentation before any provisioning decision.

Reference evidence reviewed on 2026-09-04:

- Oracle Always Free resources: https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm
- Oracle Free Tier FAQ/account requirements: https://www.oracle.com/cloud/free/faq/
- Cloudflare Tunnel Linux service: https://developers.cloudflare.com/tunnel/advanced/local-management/as-a-service/linux/
- Cloudflare Tunnel architecture: https://developers.cloudflare.com/tunnel/

Provider terms can change. Re-check primary documentation before any future activation decision.

## Cloudflare ingress option

Cloudflare Tunnel can connect outward from a future Linux host, so PersonaLattice application ports do not need public inbound firewall rules. `deploy/linux/cloudflared-config.yml.example` intentionally routes only `127.0.0.1:13000` and terminates unmatched ingress with HTTP 404. Port `18000` must never be a tunnel route.

A stable tunnel hostname can require a Cloudflare-managed hostname/zone. Do not purchase a domain under the current zero-cash policy merely to make the private beta look polished. If a genuinely zero-cash stable hostname is not already available, keep the current private-beta validation arrangement. Cloudflare Quick Tunnels remain suitable for short-lived testing only, not as the stable private-beta target.

Cloudflare ingress, if used later, is an additional network layer rather than a replacement for PersonaLattice admin authentication. The application must retain its own session and CSRF boundary.

## Backup posture

SQLite remains the correct store while the product is one-admin and measured concurrency, tenancy or HA requirements do not justify a database migration. The existing backup process creates an integrity-checked SQLite backup plus SHA-256 and release provenance, then performs a restore check before declaring success.

An off-host S3-compatible adapter may be prepared without activation, but an off-host target must not be enabled unless it has a genuine zero-cash/no-card durable path. Until then, keep verified owner-only local backups and do not treat an ephemeral free filesystem as disaster recovery.

## Future host activation gate

Do not activate a private always-on host under the current policy unless all of these are true:

1. Current official provider terms confirm no payment, card or billing activation is required.
2. Persistent storage is genuinely durable across restart/redeploy and does not silently expire under the free plan.
3. The host supports the existing one-worker architecture and protected SQLite path.
4. Exact release identity and rollback remain verifiable.
5. Web and API can stay loopback-only behind a controlled HTTPS ingress boundary.
6. Owner-only secrets remain outside Git.
7. Integrity-checked backup/restore is available before ingress changes.
8. The changed-host acceptance surface can cover anonymous denial, admin login/logout, secure cookie/CSRF mutation, one retained-case reopen, persistence across service restart, release identity, browser quick smoke and API loopback-only.

If any of those fail, the correct action is to remain on the Mac validation beta. Do not trade away persistence or security merely to obtain an “always-on” label.

A commercial multi-user launch is a different milestone. Team authorization, HA, stronger off-host backup, operational monitoring and a database migration should be justified by measured demand rather than installed pre-emptively.
