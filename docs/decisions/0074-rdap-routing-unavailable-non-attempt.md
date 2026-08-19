# ADR 0074 — RDAP bootstrap routing failure is a non-attempt source outcome

Status: accepted for RDAP activation preparation

## Context

RDAP subject lookup depends on current IANA DNS bootstrap data to select an authoritative service. That bootstrap registry is routing authority, not the subject-data provider itself.

If the bootstrap cache cannot supply a current usable registry snapshot, PersonaLattice has not contacted an authoritative RDAP service. Reporting that condition as an execution failure, remote rate limit or malformed RDAP result would therefore inflate provider-attempt and provider-failure counters.

Issue #133 also identifies a separate DOMAIN reachability gap. The graph has a DOMAIN lead kind, but the current research/evidence path is not yet a complete DOMAIN execution path. That problem is deliberately not hidden by this decision.

## Decision

Add `routing_unavailable` as an explicit reason under the existing `unavailable` source state.

A `routing_unavailable` record:

- is terminal for the current automatic source action;
- carries zero observations;
- proves no subject-provider execution attempt;
- is counted separately in deterministic source-evaluation counters;
- is intended for prerequisite routing/authority failures such as an unusable IANA RDAP bootstrap snapshot.

Add `source_routing_unavailable_record()` as the construction helper. Do not map this outcome through the generic provider-exception mapper: the whole point is that the failure happens before subject-provider execution.

## Consequences

M10/provider accounting can distinguish routing infrastructure failure from actual RDAP provider reliability. A future RDAP adapter can stop before provider execution and retain a truthful typed source state without fabricating provider contact.

The source-state vocabulary gains one non-attempt reason, so deterministic state/reason fixture coverage and evaluation projections must include it.

RDAP is still not active. `rdap_domain_registry` remains planned, unbound, source-policy-unreviewed and non-recursive until the remaining DOMAIN reachability problem is closed and the final governed activation passes review.

## Non-changes

This decision does not add a DOMAIN research route, make domain clues recursive, contact IANA or an RDAP service, add a provider descriptor or source binding, change production depth/node limits, broaden retained RDAP fields, add WHOIS/RDRS fallback, or change M5 semantics.
