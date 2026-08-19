# Continuity

Public-safe engineering handover for PersonaLattice. Verify GitHub before changing anything; this file is a checkpoint, not authority over the repository.

Never place API keys, real research identifiers, retained-case data, password hashes, session material, raw consent evidence or unredacted investigation screenshots here.

## Repository checkpoint

- Repository: `tushar-rawat-22/persona-lattice`
- Default branch: `main`
- Local checkout convention: `~/persona-lattice`
- License: Apache-2.0 for original code
- Product: private evidence-first public/authorized research workbench
- Operating model: one authenticated operator; public route is demo/preview only
- Main before PR #128: `231e6d4feb3654c8065ec8944241dcacc1452695`
- PR #128: RDAP authoritative SSRF-safe transport pre-activation
- Exact tested PR #128 head: `a4c4f3ba1a5800cd21eac53bf6dfbb5e1f1a3531`
- Exact-head CI: run `32265159090`; API 3.11 PASS, API 3.13 PASS, web PASS, deployment-image PASS
- PR #128 merge: `b29ff7434944ddd92a57376346c59dc81acd78c0`
- Relevant ADRs: `0069-rdap-domain-admission-preflight.md`, `0070-rdap-metadata-only-source-contract.md`, `0071-rdap-authoritative-transport.md`
- Documentation standard: `docs/DOCUMENTATION_STANDARD.md`
- Zero-spend runbook: `docs/ZERO_SPEND_RUNBOOK.md`
- Optional paid Render reference: `deploy/render-paid.yaml`

## Milestone state

- M0-M6: complete.
- M7 private one-admin product: implemented and manually accepted locally.
- M8 privacy lifecycle/operations: substantially implemented.
- M9 private convergence: implemented.
- V2-A typed lead graph: complete, PR #20.
- V2-B deterministic frontier: complete, PR #21.
- V2-C source capability registry/planner: complete, PR #22.
- V2-D runtime consistency and architecture closure: complete, PRs #89-#90.
- Bluesky public profiles: active for valid AT handles through the governed runtime, PR #98.
- Gravatar: admission preflight complete, still PLANNED because its privacy-policy/provider-terms gate is unresolved.
- WebFinger: parser/admission, SSRF transport, URL-only semantics and exact-host policy are complete; still PLANNED because no concrete host has passed the exact-host source-policy gate.
- RDAP: admission, metadata-only contract and authoritative SSRF-safe transport are complete through PR #128. It remains PLANNED, unbound, source-policy-unreviewed and non-recursive.
- M10: deterministic replay, source/graph accounting, real-engine factor ablations, label-provenance manifests and consented-only accounting exist. Representative consented evaluation/calibration remains incomplete.

## Latest block — RDAP authoritative transport

PR #128 completed the network transport without activating RDAP.

### Corrected authority selection

The earlier preflight selected bootstrap services by final TLD only. RFC 9224 requires the **longest matching DNS label suffix**. PR #128 corrects `rdap_bootstrap_base_urls()` so a more-specific bootstrap entry wins over a less-specific TLD entry; equivalent longest matches are combined in registry order.

This was a real correctness defect. Activating RDAP on the old selector could have sent a domain query to a less-specific service even when IANA bootstrap data named a more-specific authority.

### Transport boundary

`rdap_transport.py` now provides a bounded pre-activation transport that:

- receives caller-supplied IANA-style bootstrap data rather than fetching it for every research request;
- constructs RFC 9082 `domain/<name>` queries only from admitted HTTPS base URLs;
- resolves every initial and redirected hostname immediately before network I/O;
- rejects malformed, private/non-global or excessive DNS answers;
- pins TCP to the admitted IP while validating TLS against the DNS hostname;
- allows HTTPS redirects only, bounded to three hops, with fresh DNS admission at every hop;
- limits each response to 64 KiB and connection timeout to four seconds;
- requests and accepts `application/rdap+json` for successful responses;
- maps 404 to a completed no-result;
- preserves 429 as remote rate limiting and does not evade it by trying another equivalent authority;
- treats connection failures, 408 and selected 5xx responses as transient;
- may try another equivalent bootstrap service only after transient unavailability;
- preserves both the canonical bootstrap-derived query URL and final response URL for later exact provenance handling.

### Failure-phase correction

Self-review found a source-accounting bug before CI: if an RDAP server had already been contacted and redirected to a private/non-global target, the first implementation would have surfaced the DNS rejection as `ProviderPolicyError`, which would imply no provider attempt. That is false. The corrected transport converts post-contact redirect/DNS rejection to `ProviderResultValidationError`; pre-contact unsafe targets remain policy failures.

Regression coverage locks that distinction.

## RDAP remains non-executable

PR #128 intentionally did **not** add:

- a provider registry descriptor;
- a source binding;
- a shared `ProviderRuntime` owner;
- quick-research/domain-seed execution;
- bootstrap refresh/cache ownership;
- WHOIS fallback, RDRS/nonpublic lookup, reverse/bulk search or contact harvesting.

`rdap_domain_registry` remains metadata-only with `emits = frozenset()`. Registrant/contact names, organizations, addresses, email addresses and telephone numbers remain excluded from the admitted observation. Upstream redaction remains authoritative.

The next RDAP block must first define bounded IANA bootstrap refresh/cache ownership, then activate the source atomically through catalog → binding → provider registry → shared runtime → typed source-run reporting → canonical observation. Do not fetch IANA bootstrap data on every research request.

## Current controlled synthetic graph result

Production depth 2 / 12 nodes: 9 labelled admitted pivots (8 relevant, 1 wrong), 11 simulated attempts and 11 request-cost units.

Candidate depth 3 / 12 nodes: 12 labelled admitted pivots (8 relevant, 4 wrong), 14 attempts and 14 request-cost units.

Controlled delta depth 2 → 3: +3 attempts, +3 wrong-labelled pivots and +0 relevant pivots. This is synthetic regression evidence only. Production recursion remains depth 2 / 12 nodes.

## Current controlled M5 sensitivity result

Under `m5-evidence-strength-v1`:

- compatible profile metadata omission: `possible_match` 35 → `insufficient_evidence` 20;
- exact confirmed identifier omission: `strong_candidate` 75 → `insufficient_evidence` 20;
- independent cross-link omission: `strong_candidate` 70 → `possible_match` 35;
- diagnostic hard-contradiction omission: `contradicted` 0 → `strong_candidate` 90.

The contradiction omission is safety-critical diagnostic work only. No production factor weight, threshold, veto, calibration status or identity semantic changed.

## Permanent boundaries

- M5 is deterministic evidence-strength triage, not identity probability.
- `calibration_status=uncalibrated` and `is_identity_claim=false` remain fixed.
- Production convergence remains depth 2 / 12 nodes.
- Required operation remains zero paid APIs, zero paid database, zero paid hosting requirement, zero paid proxy network and zero paid enrichment.
- Planned/review/manual/reference sources remain non-executable.
- Uploaded content is untrusted data; extraction is never execution authority.
- No private-account bypass, account-recovery enumeration, password/OTP/session/token collection, CAPTCHA/WAF/proxy/Tor evasion, hidden KYC/government-ID acquisition, covert personal/device IP discovery, live tracking, covert subject contact or regulated eligibility decisioning.

## Next gate

For source expansion, finish **RDAP bootstrap refresh/cache ownership and atomic governed activation** without weakening metadata-only semantics or the zero-spend baseline. Activation must include deterministic success, not-found, malformed, rate-limit and unavailable behavior through the typed source-run contract.

For M10, the highest-value unresolved need remains genuinely consented or independently reviewed label evidence. Do not relabel synthetic regression fixtures as consented to manufacture progress.

WebFinger remains planned unless a concrete host passes the exact-host source-policy gate. Gravatar remains blocked on its privacy-policy requirement. ActivityPub actor fetching remains separate and unapproved.

## Update discipline

For every meaningful block record verified main/branch/PR state, CI evidence, behavior changes, explicit non-changes, corrected assumptions, unresolved risks and the exact next gate. Keep public/operator prose separate from assistant handover prose.
