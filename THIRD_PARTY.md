# Third-party boundary

PersonaLattice starts with **no vendored third-party OSINT source code or datasets**.

The project may integrate with external tools through adapters after their
license, terms, technical behavior, and privacy impact are reviewed.

| Project / source | Upstream license | Current treatment |
| --- | --- | --- |
| Maigret 0.6.3 | MIT | Reviewed M4 enrichment candidate only; not installed or executable. Any later adapter must disable recursion, AI, auto-update, proxies/Tor/I2P, bypass tooling and unrestricted all-site scans. |
| Sherlock 0.16.0 | MIT | Pinned published runtime dependency for M4. Upstream source/data are not copied into this repository. PersonaLattice reads the package's bundled dataset in place and filters it to an eight-site reviewed allowlist; it does not use Sherlock's live manifest/exclusions loader. |
| SpiderFoot | MIT | Architecture/reference study only at bootstrap |
| WhatsMyName | CC BY-SA 4.0 | Do not bundle into the Apache-2.0 tree until attribution/share-alike boundary is reviewed |
| socialscan | MPL-2.0 | Evaluation only; no copied/modified MPL files in the core |
| PhoneInfoga | GPL-3.0 | Reference only; no copied GPL code in the Apache core |
| Numverify | Provider terms | Development adapter only after provider contract review |
| Abstract | Provider terms | Development adapter only after provider contract review |
| IPQualityScore | Provider terms | Development adapter only after provider contract review |
| python-multipart 0.0.32 | Apache-2.0 | Runtime multipart parser used for bounded file intake; dependency only, not vendored |
| pypdf 6.14.2 | BSD-3-Clause | Runtime PDF text extraction inside the M2 worker boundary; dependency only, not vendored |

Sherlock's integration is intentionally narrower than its CLI defaults. The
adapter never invokes browser opening, proxies, cookies, the remote site
manifest, remote exclusions, private/authenticated account access, or a broad
unbounded site scan. Positive username hits are source observations/candidates,
not proof that an account belongs to the case subject.

The upstream repository currently declares 0.16.1, but that release was not
available from the package index during M4 CI. PersonaLattice therefore pins the
published 0.16.0 release and reviews that exact tag/package boundary rather than
silently installing an unpublished revision.

This file is an engineering control, not legal advice. Any commercial release
must re-check upstream licenses and provider/site terms at the exact versions
used.
