# GitHub exact public profile URL

Reviewed on 2026-08-21 against current GitHub REST documentation, API terms and acceptable-use rules.

## Decision

Admit an exact canonical public GitHub profile URL through the existing `github_public_api` source. This is not a second provider and does not create another quota pool.

Applicable input is only `https://github.com/<login>` with exactly one non-empty path segment, no credentials, custom port, query or fragment. A small local denylist rejects known GitHub root routes such as `search`, `settings` and `orgs` so site navigation cannot be misclassified as a person profile. Percent-encoded path segments are not treated as canonical profile URLs. PersonaLattice intentionally does not invent a stricter username grammar that could reject legacy GitHub accounts; the provider response remains authoritative for account existence.

## Provider path

The existing adapter reuses official `GET /users/{username}`. GitHub currently allows unauthenticated reads of public resources and documents a 60-request/hour unauthenticated REST limit per originating IP. Username seeds, exact profile URLs and exact repository URLs share PersonaLattice's existing one process-owned adapter and 50-request/hour local budget.

A returned profile becomes person-oriented account-candidate evidence only when:

- the returned `login` matches the requested login case-insensitively;
- GitHub returns `type == "User"`;
- the returned HTTPS `html_url` is canonical for that login.

Organization, Bot, missing or unsupported account types remain attempted result-validation failures. They do not become person evidence. A reserved/non-canonical URL is not applicable and causes no GitHub provider attempt.

## Data boundary

Profile URLs retain exactly the already-reviewed public-profile field set used by username research. This change does not add followers/org/member enumeration, repository enumeration, events, gists, commits, private resources, credentials or another contact-enrichment path. `account_candidate=true` remains evidence about the supplied public account, not an identity claim.

Repository URL behavior is unchanged. Repository-owner login remains display-only because an owner may be an organization, and repository observations emit no leads.

## Revisit conditions

Re-check GitHub API terms, acceptable-use rules, unauthenticated limits and public-user response semantics before any material scope expansion. Do not add authenticated/private-resource access or another GitHub quota owner to solve coverage gaps.