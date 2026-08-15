# ADR 0006 — governed username discovery

## Status

Accepted for M4 implementation.

## Context

M3 created a central provider execution boundary, but it deliberately left
username/social discovery non-executable. M4 needs to turn a confirmed username
into public-account evidence without making the common and dangerous leap from
"same handle exists" to "same person."

Sherlock 0.16.1 is MIT-licensed and exposes a Python username-existence engine.
Its default site loader is unsuitable for our deterministic boundary because it
can fetch a live site manifest and live exclusions. Its CLI also exposes
features PersonaLattice does not need.

Maigret 0.6.3 is also MIT-licensed and materially broader: recursive discovery,
page extraction, database auto-update, proxy/Tor/I2P paths and optional AI
analysis are available upstream. That breadth makes it a later enrichment
candidate rather than the first verifier.

## Decision

PersonaLattice integrates Sherlock first with these constraints:

1. `sherlock-project==0.16.1` is pinned.
2. Upstream source and site data are not copied into the Apache-2.0 tree.
3. The adapter reads Sherlock's packaged `resources/data.json` directly and
   selects exactly eight reviewed public sites:
   `BitBucket`, `Codeberg`, `Codeforces`, `GitHub`, `GitLab`, `Kaggle`,
   `Keybase`, and `Replit.com`.
4. `SitesInformation` is not used, so the remote manifest and remote exclusions
   are never fetched by PersonaLattice.
5. The upstream engine runs in a child process. The parent exposes only a small
   JSON machine contract and kills the child when M3 timeout cancellation
   occurs. This avoids leaving a synchronous network scan running after the
   governed execution deadline.
6. No proxy, browser-open, cookie/login, private-account, CAPTCHA/WAF-bypass or
   account-contact option exists in the adapter contract.
7. Positive, negative, illegal, WAF and unknown outcomes are retained
   explicitly. Full response bodies are not returned or persisted.
8. A positive hit becomes a provider Observation with
   `account_candidate=true` and `identity_claim=false`. Correlation belongs in
   M5.
9. M3 centrally rejects non-username identifiers before the Sherlock adapter is
   called.
10. User-supplied usernames and human-confirmed M2 username candidates remain
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
