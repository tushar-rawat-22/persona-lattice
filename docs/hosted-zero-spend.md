# Zero-spend hosted architecture

PersonaLattice has two deliberately different deployment classes.

The **public observer** is the canonical always-on public link. It is a static Cloudflare Pages export containing synthetic fixtures only. It must not depend on the founder Mac, run providers, accept uploads, expose retained cases, or contain a private API origin or credential.

The **private beta** is a one-admin authenticated evidence workspace with persistent SQLite. The current Mac/ngrok deployment is validation infrastructure: it is allowed to be offline while the Mac sleeps and must never be marketed as an always-on service.

## Zero-cash rule

Current infrastructure decisions must cost ₹0. Do not require a purchased domain, paid database, paid storage, billing-enabled hosting, or a paid uptime tier. Prepare migration and recovery artifacts before asking the founder to activate any provider account.

Free stateless web hosts are not acceptable for the retained private-beta database when their local filesystem is ephemeral or disappears during spin-down/redeploy. Persistence and recovery are product requirements, not optional hosting details.

## Provider-neutral Linux bundle

`deploy/linux/` prepares the current one-admin architecture for a small Linux VM without changing application authority:

- an exact-SHA release checkout under `/opt/persona-lattice/releases/`;
- a dedicated `personalattice` system user;
- owner-only configuration at `/etc/persona-lattice/production.env`;
- persistent SQLite under `/var/lib/persona-lattice/data/`;
- release-specific prepared runtime state under `/var/lib/persona-lattice/runtime/<sha>/`;
- a systemd service with restart-on-failure and basic process hardening;
- web bound only to `127.0.0.1:13000`;
- API bound only to `127.0.0.1:18000` and reachable externally only through the web `/api` proxy;
- the existing SQLite integrity-checked backup/restore contracts through Linux wrappers;
- a host verifier that checks release identity, service health, same-origin API health and loopback-only listeners;
- an optional Cloudflare Tunnel configuration that publishes the web port only.

Preparation is intentionally release-addressed. `prepare-release.sh <full-sha>` builds a release before switching `/opt/persona-lattice/current`; the same command with a previously accepted SHA is the rollback mechanism. The runtime user does not own the prepared source tree after preparation.

The environment template contains placeholders only. A real password hash, provider key, tunnel token or tunnel credential file must never be committed.

## First stable-host candidate: OCI Always Free

Oracle Cloud Infrastructure is the first zero-cash VM candidate to attempt because Oracle currently documents Always Free compute and persistent block storage. That is a candidate, not an availability promise. Oracle also documents capacity limitations for Always Free compute, and account/signup availability can block provisioning.

The Linux bundle therefore does not contain OCI-specific application logic. If an OCI Always Free VM can be provisioned, install a supported Python/Node/Git toolchain, copy the owner-only environment file, then run the exact-SHA preparation script. If provisioning is unavailable, remain on the accepted Mac private beta rather than weakening persistence or security on an ephemeral host.

Reference evidence (reviewed 2026-09-04):

- Oracle Always Free resources: https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm
- Cloudflare Tunnel Linux service: https://developers.cloudflare.com/tunnel/advanced/local-management/as-a-service/linux/
- Cloudflare Tunnel architecture: https://developers.cloudflare.com/tunnel/

Provider quotas and free-tier terms can change. Re-check official provider documentation immediately before any founder signup or deployment decision.

## Cloudflare ingress option

Cloudflare Tunnel can connect outward from the VM, so the PersonaLattice application ports do not need public inbound firewall rules. `deploy/linux/cloudflared-config.yml.example` intentionally routes only `127.0.0.1:13000` and terminates unmatched ingress with HTTP 404. Port `18000` must never be a tunnel route.

A stable tunnel hostname may require a Cloudflare-managed hostname/zone. Do not purchase a domain merely to make the private beta look polished. If a zero-cash stable hostname is not already available, keep the existing private-beta ingress until a justified option exists. Cloudflare quick tunnels are useful for testing but are not the stable private-beta target.

## Backup posture

SQLite remains the correct store while the product is one-admin and measured concurrency/tenancy/HA requirements do not justify a database migration. The existing backup process creates an integrity-checked SQLite backup plus SHA-256 and release provenance, then performs a restore check before declaring success.

An off-host object-store adapter can be prepared later, but activation requires a genuinely zero-cash durable target. Until then, keep verified owner-only local backups and do not pretend an ephemeral free filesystem is disaster recovery.

## Activation gate

Before moving the accepted private beta from the Mac to any Linux VM:

1. Re-check current provider free-tier, capacity and account requirements from official sources.
2. Provision only a zero-cash VM/storage combination; stop if billing or purchase becomes required.
3. Install the required runtime toolchain without changing PersonaLattice's application contracts.
4. Create `/etc/persona-lattice/production.env` from the example, fill secrets outside Git, set mode `600`.
5. Run `sudo bash deploy/linux/prepare-release.sh <accepted-release-sha>` from a trusted checkout.
6. Run `sudo bash /opt/persona-lattice/current/deploy/linux/verify-host.sh <accepted-release-sha>`.
7. Run and retain one integrity-checked backup before changing ingress.
8. If Cloudflare Tunnel is available at zero cash, publish only the loopback web origin and keep API `18000` un-routed.
9. Perform only the changed-host acceptance surface: anonymous denial, admin login/logout, secure cookie/CSRF mutation, one retained-case reopen, persistence across service restart, release identity, browser quick smoke, and API loopback-only. Reuse unchanged application-contract evidence rather than rerunning unrelated broad suites.

A commercial multi-user launch is a different milestone. Team authorization, HA, stronger off-host backup, operational monitoring and a database migration should be justified by measured demand rather than installed pre-emptively.
