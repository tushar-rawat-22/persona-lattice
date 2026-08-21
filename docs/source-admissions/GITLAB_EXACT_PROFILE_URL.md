# GitLab exact public profile URL admission

Status: **active through the existing `gitlab_public_api` source when merged**.

Reviewed against current GitLab primary documentation on 2026-08-21: Users API, user-profile routing, reserved top-level routes, API Terms of Use, Acceptable Use Policy, and current rate-limit guidance.

## Applicability

Only an explicit canonical `https://gitlab.com/<username>` URL is eligible. The path must contain exactly one non-empty segment. Credentials, custom ports, query strings, fragments, percent-encoded path segments, `/-/u/<id>`, multi-segment routes, and GitLab's documented reserved top-level routes are rejected locally before provider execution.

The username segment must also satisfy GitLab's current canonical slug shape: 2-255 characters, alphanumeric at both ends, only alphanumerics plus single `.`, `_`, or `-` separators internally. Noncanonical one-segment paths are rejected before provider contact rather than spent against the shared API budget.

A one-segment GitLab path can identify a group namespace. PersonaLattice therefore does not infer that the URL represents a person. It performs one exact human-only username lookup and treats no matching human as a completed no-match.

## Provider execution

The extension reuses the existing `gitlab_public_api` adapter, provider descriptor, process-wide runtime owner, and 20-request/minute local budget already shared by username, exact public-email, and exact public-project research. It does not create another provider, credential path, or quota bucket.

Profile URLs reuse the official `GET /users?username=<username>&humans=true` path. Returned evidence must match the requested username case-insensitively and provide a canonical `https://gitlab.com/<username>` `web_url`; otherwise the result fails closed after the attempt.

## Retained evidence

The reviewed GitLab public-profile field set is unchanged. The observation remains an account candidate, not an identity claim. No new social, activity, project/member, private-email, credential, or contact-enrichment fields are introduced by URL admission.

Exact public project and subgroup-project behavior is unchanged. Project metadata remains display-only and emits no leads.

## Explicit exclusions

PersonaLattice does not use GitLab user search by free text, profile scraping, `/-/u/<id>` routing, group-to-person inference, members/contributors, repository contents, commits, issues/MRs, releases, pipelines/jobs, packages, private resources, or additional GitLab traffic budgets through this extension.
