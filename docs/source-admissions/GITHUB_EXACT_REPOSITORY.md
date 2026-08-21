# GitHub exact public repository admission

Reviewed on 2026-08-21 from GitHub's current REST documentation and API terms.

## Decision

Extend the existing `github_public_api` source to exact public repository URLs. This is not a new provider and does not receive a second quota bucket.

PersonaLattice accepts only `https://github.com/<owner>/<repo>` with exactly two path segments and no credentials, custom port, query string, fragment or extra route. An applicable URL uses only GitHub's official `GET /repos/{owner}/{repo}` endpoint. Public repository retrieval can be used without authentication.

GitHub currently limits unauthenticated REST traffic to 60 requests per hour per originating IP. PersonaLattice keeps the existing `github_public_api` budget at 50 requests per hour, one attempt, a 4-second timeout, a 64 KiB response ceiling and concurrency two. Username-profile and repository requests therefore compete for the same process-owned budget instead of multiplying traffic.

## Retained evidence

Repository observations retain only:

- canonical repository `full_name`;
- exact owner login;
- owner type when it is `User` or `Organization`;
- an explicit public-state check (`private=false`);
- `fork` and `archived` booleans when supplied;
- canonical public repository locator;
- `identity_claim=false`.

Description, homepage, topics, language, license/content, popularity counters, issue counts, branches, timestamps, avatars, contributor/member lists, commits, issues, releases, repository contents, email and other contact-like fields are not admitted.

`github_repository_owner_login` is display-only. Repository owners can be organizations, so the adapter does not turn the owner into a username pivot. Repository observations emit no leads.

## Failure semantics

- `404`: completed no-match after a provider attempt.
- `403` with exhausted GitHub rate budget, or `429`: remote rate limit; valid `Retry-After` is preserved.
- `408`, 5xx and network failures: attempted transient/unavailable result.
- malformed or oversized responses: attempted validation failure.
- a private result, mismatched `full_name`, mismatched owner, unsupported owner type or mismatched canonical locator: fail closed.

The source does not perform repository, code or topic search; owner or organization enumeration; member/contributor lookup; commit, issue, release or content retrieval; or private-resource access.

## Product boundary

This extension adds exact public repository context without adding credentials, spend, a new network provider or a new request allowance. Existing username-profile behavior remains unchanged. The required PersonaLattice baseline remains ₹0.