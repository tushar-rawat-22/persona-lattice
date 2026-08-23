# Zero-spend source admission matrix

This file is a research queue, not an execution allow-list. A candidate appearing here does not make it eligible for runtime use.

PersonaLattice keeps the current source freeze until Launch Candidate 1 and the operator-workspace redesign are complete. After that point, a source can become executable only through the normal catalog, binding, registry, `ProviderRuntime`, typed source-state and canonical-evidence path. Each target still needs its own terms, privacy, authentication, rate-limit, contact-risk and failure-semantics review.

## Current candidates

| Candidate | Cost / auth | Potential value | Main risk | Decision before LC1 |
| --- | --- | --- | --- | --- |
| WebFinger (RFC 7033) | Protocol itself is free; exact host/resource query | Exact discovery for already-known URI-style identities such as `acct:` identifiers, with structured JRD links and properties | The RFC explicitly warns about privacy and recommends clients avoid queries unless authorized; returned information is not guaranteed accurate | **Review after LC1.** Exact known-resource queries only. No guessing, reverse enumeration, HTTP downgrade or identity-proof semantics |
| WhatsMyName dataset | Free dataset; CC BY-SA 4.0 | Maintained catalogue of hundreds of public username-profile checks, useful for discovering candidate sites and detection patterns | Dataset inclusion is not permission to query a site; each site has independent terms, rate limits and false-positive behavior | **Catalogue input only.** Never import the full dataset as executable providers |
| Maigret public project/database | MIT project; no key required for many checks | Large site catalogue and useful examples of profile parsing, site metadata and graph-oriented reporting | Default/recursive behavior is far broader than PersonaLattice policy, including mass checks, recursion, Tor/I2P support and block-bypass features | **Research input only.** Do not embed unrestricted execution, recursion, permutation, CAPTCHA/block bypass or 500/3000-site fan-out |
| Gravatar Profiles API | Free; 100 profile requests/hour unauthenticated, 1000/hour with API key | Public profile metadata from an exact known profile identifier or SHA-256 of an already-known email | Email hashing can become enumeration if misused; authenticated endpoints expose additional contact/payment/wallet fields that are outside the intended public-profile scope | **Medium-priority review after LC1.** Exact known input only; public profile fields only; no contact/payment/wallet expansion |
| RDAP | Standards-based HTTP service; existing PersonaLattice domain path is preferred | Structured public registration data and typed registration states | Differentiated/non-public registration access must stay out of scope; registration data is not proof about a natural person | **Keep existing governed path.** Do not add generic WHOIS scraping as a parallel source |
| Telegram Bot API | Free API but requires a bot token | Useful for bots inside chats they legitimately participate in | Official bot access is chat-context based, bots cannot start arbitrary conversations with users, and privacy mode limits group visibility. It is not a general people-search API | **Reject as generic people-search source.** No third-party bots, user-account automation, group-member scraping or message harvesting |
| Exact public profile endpoints | Usually free HTTP/API paths; source-specific | High value when an already-known canonical profile URL can be validated by the site itself | Terms, auth, anti-automation rules and false-positive semantics vary by site | **Review one site at a time after LC1.** Exact canonical profiles only unless a separate identifier capability passes review |
| Public archival metadata | Usually free/bounded endpoints | Capture availability/timestamps and historical public-URL evidence | Archived content can be stale or sensitive; availability is not identity proof | **Keep metadata-only behavior.** No broad archival scraping without a separate review |

## Admission rules

1. Required spend must remain ₹0 for the private beta.
2. A source must have a narrow, documented identifier contract. “Search the internet for this person” is not a contract.
3. Publicly accessible does not mean automatically permissible for automated execution. Site-specific terms and rate limits still control admission.
4. Every runtime attempt must produce a typed state such as executed, not-found, unavailable, blocked, review-required or rate-limited. Silent failure is not acceptable.
5. Same-handle or same-email-derived profile results remain account candidates, not identity claims.
6. No source may introduce private-account bypass, credential/OTP/token collection, hidden KYC or government-ID acquisition, personal-device IP inference, live location, contact harvesting, non-public registration access, bulk/reverse enumeration or regulated decisioning.
7. Recursive pivots remain bounded by the existing depth/node budget. A third-party tool's broader recursion policy is not inherited.
8. Dataset projects such as WhatsMyName and Maigret are discovery inputs. Executable targets are admitted individually and tested independently.
9. One new zero-spend source at a time after LC1, with exact-head CI before merge.

## Primary references used for this pass

- RFC 7033, WebFinger: https://www.rfc-editor.org/rfc/rfc7033.html
- WhatsMyName: https://github.com/WebBreacher/WhatsMyName
- Maigret: https://github.com/soxoj/maigret
- Gravatar REST API: https://docs.gravatar.com/rest-api/
- Telegram bot introduction and privacy behavior: https://core.telegram.org/bots and https://core.telegram.org/bots/faq

The next useful research pass is not to add more names to this table. It is to take the highest-value exact public-profile candidates from the catalogue projects and review their primary site terms one by one, then rank them by coverage gained per request, maintenance burden and contact/privacy risk.