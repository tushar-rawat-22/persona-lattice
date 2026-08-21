# Third-party boundary

PersonaLattice starts with **no vendored third-party OSINT source code or datasets**.

The project may integrate with external tools through adapters after their
license, terms, technical behavior, and privacy impact are reviewed.

| Project / source | Upstream license / terms | Current treatment |
| --- | --- | --- |
| Maigret 0.6.3 | MIT | Reviewed M4 enrichment candidate only; not installed or executable. Any later adapter must disable recursion, AI, auto-update, proxies/Tor/I2P, bypass tooling and unrestricted all-site scans. |
| Sherlock 0.16.0 | MIT | Pinned published runtime dependency for M4. Upstream source/data are not copied into this repository. PersonaLattice reads the package's bundled dataset in place and filters it to an eight-site reviewed allowlist; it does not use Sherlock's live manifest/exclusions loader. |
| SpiderFoot | MIT | Architecture/reference study only at bootstrap |
| WhatsMyName | CC BY-SA 4.0 | Do not bundle into the Apache-2.0 tree until attribution/share-alike boundary is reviewed |
| socialscan | MPL-2.0 | Evaluation only; no copied/modified MPL files in the core |
| PhoneInfoga | GPL-3.0 | Reference only; no copied GPL code in the Apache core |
| Keybase public user API | Keybase Terms of Service / Acceptable Use Policy | Active only for already-canonical Keybase usernames. Uses the credentialless official user lookup with `fields=basics`, retaining only username, public UID, account creation timestamp and canonical profile provenance. Profile text, proofs, external identities, keys, cryptocurrency addresses and contact-like data are not requested or admitted. Same-handle evidence remains an account candidate, not an identity claim. No Keybase code or dataset is vendored. |
| Stack Exchange API / Stack Overflow | Stack Exchange API Terms of Use | Active only for exact numeric Stack Overflow profile URLs. Uses anonymous official `/users/{id}` reads, keeps visible Stack Overflow attribution and canonical provenance, retains bounded account metadata only, and never uses fuzzy `inname` search. No API content or code is vendored. |
| OpenAlex | CC0 data; OpenAlex API terms/pricing | Active only for exact `https://openalex.org/A…` author URLs when a free server-side API key is configured. Uses the official singleton author endpoint with bearer authentication, retains bounded CC0 scholarly-profile metadata only, and performs no name/ORCID search, affiliation expansion, work enumeration or emitted-lead discovery. No OpenAlex data or code is vendored. |
| Wikidata | CC0 structured data; Wikimedia API usage/User-Agent/rate-limit policies | Active only for exact `https://www.wikidata.org/wiki/Q…` item URLs. Uses official `wbgetentities` reads with a compliant identifying User-Agent, retains bounded English label/description metadata plus canonical QID provenance, performs no entity search/claims expansion/external-ID extraction, and emits no leads. No Wikidata data or code is vendored. |
| Crossref REST API | Crossref REST API and metadata reuse guidance | Active only for exact `https://doi.org/<doi>` URLs. Uses credentialless singleton `/works/{doi}` reads, retains bounded bibliographic facts and display-only author names, excludes abstracts, external author IDs, affiliations, references and full-text/resource expansion, and emits no leads. No Crossref code or dataset is vendored. |
| Hacker News API | Y Combinator Terms of Use | Rejected for the intended commercial product path under current terms; do not activate merely because the API is public and credentialless. |
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
