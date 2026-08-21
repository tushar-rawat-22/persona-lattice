# GitLab exact public project admission

Reviewed 2026-08-21 for the existing `gitlab_public_api` source.

PersonaLattice may read public GitLab.com project metadata only when the operator supplies an exact canonical project URL of the form `https://gitlab.com/<namespace>/<project>`. The first version accepts exactly two path segments. Subgroup projects are intentionally not applicable until a local path rule can distinguish nested namespaces from project routes without guessing.

GitLab's current REST documentation permits unauthenticated `GET /projects/:id` reads for public projects and accepts a URL-encoded project path as `:id`. GitLab.com documents unauthenticated traffic limits well above PersonaLattice's existing 20 requests/minute provider budget. This extension therefore reuses the existing process-owned adapter, concurrency limit and rate bucket; it does not add a credential or another GitLab quota pool.

## Retained evidence

For an admitted exact public project, keep only:

- numeric project ID;
- exact `path_with_namespace`;
- explicit `visibility=public`;
- bounded namespace kind and exact namespace full path;
- optional archived flag;
- canonical `web_url` provenance;
- `identity_claim=false`.

Description, README/repository content, topics, language, license data, stars/forks/watchers, issue or merge-request counts, timestamps, avatars, owner/person metadata, contributors/members, commits, releases, branches/tags, pipelines/jobs, packages, emails and contact-like material are not retained.

The retained project keys are provider-specific and intentionally absent from the generic lead extractor. Project observations emit no recursive leads. A namespace may be a user or a group, so namespace context is display evidence rather than a person pivot.

## Execution boundary

The source calls only `GET /api/v4/projects/{URL-encoded namespace/project}`. It does not use project/group search, autocomplete, owner/member enumeration, repository contents, commits, issues, merge requests, releases, branches/tags, pipelines, jobs, packages or private resources.

A non-applicable URL causes no GitLab provider attempt. `404` is a completed no-match. `429` preserves a valid `Retry-After`. `408`, `5xx` and network failures remain attempted transient failures. Oversized or malformed responses, non-public visibility, malformed namespace metadata, path mismatch or canonical-URL mismatch fail closed after an attempt.

Existing username and exact-public-email behavior is unchanged. All three GitLab identifier kinds share one provider descriptor and one process-owned runtime adapter with one attempt, a 4-second timeout, a 64 KiB response ceiling, concurrency 2 and a 20 requests/minute local budget.

This review authorizes only the bounded path above. It does not authorize subgroup-path inference, fuzzy project discovery or new recursive identity behavior.
