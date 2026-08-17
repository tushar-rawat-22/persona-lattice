# ADR 0025 — Quick research emits factual source-run records

Status: accepted for V2-D architecture closure

## Context

Converged nodes already have a privacy-bounded `source_runs` projection, but the normal quick-research path still returned only observations and warning strings. That meant real execution facts disappeared before convergence could retain them.

Warnings are not a safe substitute. A source can return no match, be unavailable before any request, stop at a local budget, fail after execution begins, or return observations. Those cases have different operational meanings even when the user-facing warning is similar.

## Decision

`QuickResearchReport` now carries typed `SourceRunRecord` values produced at the point where the execution outcome is known.

Current quick research records:

- successful local deterministic work as `executed`;
- completed zero-result lookups as `not_found`;
- optional Brave search with no configured key as `unavailable / optional_not_configured`, with no execution attempt;
- local rate-budget exhaustion as `budget_stopped / local_budget`, with no provider attempt;
- remote rate limits as attempted `unavailable / remote_rate_limit`;
- proven post-entry execution failures as attempted `unavailable / execution_failure`.

The implementation deliberately does not convert every exception into an attempted provider failure. Policy, authentication and preflight validation failures can happen before network execution, so an exception is recorded only when the boundary proves the relevant execution fact. Existing warning behavior remains for operator-readable failure text.

Injected compatibility lookups are treated as logical source attempts when they are actually invoked. They remain test/compatibility seams and do not become production runtime owners.

## Optional public search

The existing Brave path remains optional and legacy for now. If the default search function is selected and no `BRAVE_SEARCH_API_KEY` is configured, quick research records `optional_not_configured` instead of incorrectly reporting `not_found`. This preserves the zero-spend baseline and avoids pretending an unqueried source returned a negative result.

No new provider, endpoint, key, paid dependency or source coverage is activated by this change.

## Privacy and compatibility

Source-run records contain source name, lead kind, state/reason and observation count only. They do not copy identifier values, source locators, provider payloads, credentials or exception text.

`source_runs` is additive and defaults to an empty tuple, so older direct `QuickResearchReport` construction remains valid.

## Consequences

Normal converged research can now populate its existing source-run projection from actual quick-research facts instead of an empty compatibility placeholder. Reliability and budget measurements can distinguish provider behavior from local policy/configuration decisions.

The next architecture block should tighten completeness: define explicit typed outcomes for pre-execution policy/configuration failures and malformed-result handling where the current execution boundary cannot yet prove a state, then add evaluation counters over the retained source-run projection.
