# Current release status

This file is a narrow, current release-status checkpoint for PersonaLattice. It does not replace the architectural history in `docs/CONTINUITY.md`, `docs/ROADMAP.md`, or `docs/LIVE_BETA.md`; where those documents contain older release checkpoints, this file and fresh GitHub/provider evidence take precedence until the next material documentation consolidation.

Last reviewed against GitHub authority: 2026-09-08.

## Canonical authority

- Repository: `tushar-rawat-22/persona-lattice`
- Canonical branch: `main`
- Exact main / current private-beta release under acceptance: `758b6ae3e96691e7f4880524e1ea49b826da0508`
- Operational rollback: `8b773b4dc1560ab1160f1a3ce30705f6a4bae179`
- Runtime-manifest parent rollback: `4c0b05d4a0ae6215d8e1b884c78ef10f14432847`
- Exact-main CI #2995: passed
- Current external-operator gate: Issue #340, Tranche A PARTIAL
- External operator beta: **NO-GO**

PR #344 fixed a P1 deployment-contract defect discovered during Tranche A: the Git-tracked `0644` private-beta preparation runner must be invoked explicitly through Bash. The targeted launchd regression passes on current main. Deployment preflight must continue to verify executable-vs-interpreter invocation semantics before live bootstrap.

### Release-governance gap

GitHub currently reports `main` as unprotected and the repository has no active repository ruleset. The release process therefore relies on operator discipline rather than a server-side control to prevent an accidental direct push from moving the exact acceptance target. This does not invalidate evidence already tied to unchanged `758b6ae3e96691e7f4880524e1ea49b826da0508`, but it is a real release-governance weakness.

The smallest eventual correction is a repository-admin branch protection/ruleset that requires pull-request based changes and the established CI checks before `main` moves. Do not change the accepted Tranche-A release merely to document or remediate this governance gap, and do not claim the server-side control exists until GitHub authority confirms it.

## Public observer

The canonical public observer is `https://persona-lattice.pages.dev`.

It must remain:

- synthetic and sanitized;
- read-only;
- independent of the founder Mac;
- free of private case data, provider credentials, private source execution, retained-case identifiers, mutation authority, and private-beta hostnames.

GitHub/Cloudflare deployment evidence ties the public Pages deployment to exact main `758b6ae3e96691e7f4880524e1ea49b826da0508`. A deployment/control-plane success is release-identity evidence, not a substitute for a fresh independent HTTP/browser reachability check when making a live-availability claim.

## Private beta

The current private analyst runtime is a protected one-admin validation runtime and remains **MAC-DEPENDENT**. It is not truthful 24/7 hosting and must not be represented as such.

Accepted evidence that may be reused while its inputs remain unchanged:

- API/web loopback-only boundary;
- persistent SQLite path/mode/inode invariants;
- Safari authentication;
- retained safe-case reopen;
- Chrome login;
- Chrome 390px and 320px viewport acceptance;
- Chrome keyboard focus acceptance.

Tranche A still requires:

1. complete and inspect one new bounded safe case;
2. add an analyst decision and verify reload retention;
3. search and reopen the retained case;
4. inspect synopsis/handoff;
5. review export and checksum;
6. verify logout denial and stale-UI behavior;
7. restart, re-authenticate, and prove case/decision/provenance persistence;
8. complete the authenticated Chrome journey;
9. complete the remaining Safari journey plus narrow viewport/keyboard checks.

Those remaining acceptance items require the protected local runtime/browser environment and are **MAC-DEPENDENT**. While they are blocked, safe GitHub/cloud/provider/documentation/release-truth work may continue provided it does not move the accepted private release, begin Tranche B, advance Issue #222 source expansion, or change operator-visible behavior. Do not begin Tranche B or Issue #222 source expansion automatically.

## Next gates

After Tranche A closes, Tranche B covers degraded-source and evidence-integrity attacks: no-match, blocked/rate-limit/timeout/malformed/partial outage/all-unavailable, stale/duplicate/conflicting evidence, weak-vs-strong correlation, and deliberate false-correlation/M5 semantics. Provider failure must never become identity evidence.

Tranche C then covers the remaining destructive/recovery/session/browser matrix and the final external-operator GO/NO-GO evidence.

## Zero-cash and authority boundary

No paid or billing-enabled service may be activated without explicit founder approval. Do not weaken persistence, authentication, API isolation, backup/restore, release identity, or HTTPS requirements merely to claim always-on availability.

The public observer and private beta are separate authority surfaces. A public deployment must never acquire private operator authority.
