# Third-party boundary

PersonaLattice starts with **no vendored third-party OSINT source code or datasets**.

The project may integrate with external tools through adapters after their
license, terms, technical behavior, and privacy impact are reviewed.

| Project / source | Upstream license | Initial treatment |
| --- | --- | --- |
| Maigret | MIT | Candidate optional adapter; do not vendor during bootstrap |
| Sherlock | MIT | Candidate optional adapter; do not vendor during bootstrap |
| SpiderFoot | MIT | Architecture/reference study only at bootstrap |
| WhatsMyName | CC BY-SA 4.0 | Do not bundle into the Apache-2.0 tree until attribution/share-alike boundary is reviewed |
| socialscan | MPL-2.0 | Evaluation only; no copied/modified MPL files in the core |
| PhoneInfoga | GPL-3.0 | Reference only; no copied GPL code in the proprietary/product core |
| Numverify | Provider terms | Development adapter only after provider contract review |
| Abstract | Provider terms | Development adapter only after provider contract review |
| IPQualityScore | Provider terms | Development adapter only after provider contract review |
| python-multipart 0.0.32 | Apache-2.0 | Runtime multipart parser used for bounded file intake; dependency only, not vendored |
| pypdf 6.14.2 | BSD-3-Clause | Runtime PDF text extraction inside the M2 worker boundary; dependency only, not vendored |

This file is an engineering control, not legal advice. Any commercial release
must re-check upstream licenses and provider terms at the exact versions used.
