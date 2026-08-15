# ADR 0006 — governed username discovery

## Status

Accepted for M4 implementation.

## Context

M3 created a central provider execution boundary, but it deliberately left
username/social discovery non-executable. M4 needs to turn a confirmed username
into public-account evidence without making the common and dangerous leap from
"same handle exists" to "same person."

The Sherlock repository currently declares 0.16.1, but CI verified that the
package index exposes releases only through 0.16.0. M4 therefore pins and
reviews the published Sherlock 0.16.0 release rather than depending on an
unpublished repository version. Sherlock is MIT-licensed and exposes a Python
username-existence engine. Its default site loader is unsuitable for our
deterministic boundary because it can fetch a live site manifest and live
exclusions. Its CLI also exposes features PersonaLattice does not need.

Maigret 0.6.3 is also MIT-licensed and materially broader: recursive discovery,
page extraction, database auto-update, proxy/Tor/I2P paths and optional AI
analysis are available upstream. That breadth makes it a later enrichment
candidate rather than the first verifier.

## Decision

PersonaLattice integrates Sherlock first with these constraints:

1. `sherlock-project==0.16.0` is pinned.
2. Upstream source and site data are not copied into the Apache-2.0 tree.
3. The adapter reads Sherlock's packaged `resources/data.json` directly and
   selects exactly eight reviewed public sites: `BitBucket`, `Codeberg`,
   `Codeforces`, `GitHub`, `GitLab`, `Kaggle`, `Keybase`, and `Replit.com`.
4. `SitesInformation` is not used, so the remote manifest and remote exclusions
   are never fetched by PersonaLattice.
5. The upstream engine runs in a child process. Parent-to-worker IPC carries
   only the username, approved site names and timeout; it never carries site
   URLs or request metadata. The worker independently reloads the exact pinned
   package data and refuses any site outside the same hard-coded allowlist.
6. M3 timeout cancellation kills and reaps the child process. A timed-out
   synchronous scan therefore cannot continue issuing requests in a background
   thread after the governed execution has ended.
7. No proxy, browser-open, cookie/login, private-account, CAPTCHA/WAF-bypass or
   account-contact option exists in the adapter contract.
8. Positive, negative, illegal, WAF and unknown outcomes are retained
   explicitly. Full response bodies are not returned or persisted.
9. A positive hit must include a valid public HTTP(S) profile URL and becomes a
   provider Observation with `account_candidate=true` and
   `identity_claim=false`. Correlation belongs in M5.
10. M3 centrally rejects non-username identifiers before the Sherlock adapter
    is called.
11. User-supplied usernames and human-confirmed M2 username candidates remain
    the only permitted query origins.

## Why not use Sherlock's live default dataset?

A pinned Python package is not enough if the site catalog can change at runtime.
Using the packaged catalog plus a fixed allowlist keeps the reviewed network
surface deterministic until we explicitly change the dependency or allowlist.

## Why a child process?

Sherlock's core function is synchronous. Running it with `asyncio.to_thread`
would allow M3's coroutine timeout to return while the underlying thread kept
issuing requests. A killable worker process gives the timeout boundary actual
control over the network activity.

Passing only approved site names across IPC is deliberate defense in depth. It
prevents the internal worker boundary from becoming an arbitrary-URL transport
if a future caller is wired incorrectly.

## Maigret

Maigret remains non-executable in M4 until a separate constrained adapter proves
that recursion, AI mode, auto-update, proxies/Tor/I2P, bypass tooling and broad
all-site scans are disabled. It must reuse M3 rather than creating a parallel
execution path.

## Consequences

- M4 starts with a deliberately small public-account surface.
- Site coverage is lower than upstream Sherlock, by design.
- Site behavior can still change independently and produce unknown/false
  positive/false negative observations; M5 must not treat a hit as identity
  proof.
- Any allowlist expansion is a source-policy change and needs review.
