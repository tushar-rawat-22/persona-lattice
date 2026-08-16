# ADR 0010 — Recursive evidence lead graph

Status: accepted for V2 foundation

## Context

PersonaLattice can already start from a username, email, phone number or URL and
follow a small set of attributable public fields. The current convergence loop is
intentionally narrow: it has a fixed depth/node budget and a hard-coded list of
fields that may become another lookup.

That shape was correct for proving the private V1 product, but it is too brittle
for a larger evidence-intelligence system. Adding more providers directly to the
loop would create several problems:

- provider payload keys would become part of orchestration policy;
- different sources could normalize the same clue differently;
- a newly added field could accidentally trigger recursive collection;
- contextual facts such as a location or employer could be mistaken for strong
  identifiers;
- sensitive fields could be copied into the graph before policy had a chance to
  reject them;
- future cost/rate/provider controls would be scattered across adapters;
- recursive expansion could become non-deterministic or unbounded.

The next architecture therefore separates **evidence**, **leads**, **execution**
and **correlation**.

## Decision

Introduce a typed evidence-lead layer between provider observations and recursive
research execution.

A provider observation remains evidence. A lead is only a candidate next step
extracted from that evidence. A lead is never an identity conclusion.

The V2 research pipeline is:

1. accept one or more operator-authorized seed clues;
2. normalize supported identifiers with the existing M1 normalization rules;
3. execute only providers allowed by purpose, consent, source policy and budget;
4. store each result as a provenance-bearing observation;
5. extract typed leads from an exact allowlist of reviewed public fields;
6. classify every lead as `auto_pivot`, `review_required`, `display_only` or
   `blocked`;
7. enqueue only `auto_pivot` leads within deterministic depth/node/source/cost
   limits;
8. retain parent/child provenance for every edge;
9. repeat until the frontier is exhausted or a budget is reached;
10. evaluate candidate-account evidence with the existing M5 engine;
11. render gaps, contradictions, stale evidence and unexecuted leads alongside
    positive findings.

## Lead classes

The foundation recognizes these lead kinds:

- username
- email
- phone
- URL
- domain
- name
- organization
- location

The list is deliberately broader than the list of automatically executable
research seeds. Representation and execution are separate decisions.

Initial policy:

| Lead | Default disposition | Rationale |
| --- | --- | --- |
| explicitly public email | auto pivot | attributable identifier with existing exact-match research path |
| explicitly public username | auto pivot | attributable identifier; account candidate only |
| explicitly public URL | auto pivot | attributable public resource |
| phone discovered in another source | review required | higher sensitivity/contact risk; do not silently fan out |
| domain | display only initially | useful context; domain intelligence gets its own reviewed adapter set |
| name | display only | high collision rate |
| organization | display only | contextual evidence, not a unique identifier |
| location/region | display only | contextual evidence, not a unique identifier |

A seed phone number may still be researched because the operator explicitly chose
it as the starting identifier. The rule above applies to newly discovered phone
numbers.

## Sensitive-field fail-closed rule

The lead extractor never copies values from fields representing government IDs,
credentials, OTPs, authentication tokens or personal/device IP addresses into the
recursive lead graph. It may record the blocked **field name** for audit/debugging
without retaining the value.

This means a future adapter cannot make an Aadhaar number, password, token or
personal IP address part of autonomous convergence merely by returning a new JSON
field.

Public website infrastructure IP addresses may remain source observations when
collected as infrastructure metadata, but they are not person/device leads.

## Normalization

There is one normalization authority.

Username, email, phone, URL, name and organization leads reuse the M1 evidence
normalizer. The recursive graph must not introduce a second identity-equivalence
policy.

In particular, generic username values and email local-parts are **not**
case-folded. Provider-specific equivalence belongs in the provider adapter or a
future reviewed provider-specific rule.

This corrects an assumption in the original V1 convergence node key, which used a
generic `casefold()` for all research kinds even though M1 explicitly rejected
that behavior.

## Provenance model

Each graph edge keeps:

- parent lead key;
- child lead key;
- extraction reason;
- provider/source name;
- source locator;
- originating field name in the internal lead contract.

This follows the same principle as W3C PROV: derivation must remain traceable to
entities/activities that produced it. PersonaLattice does not need to serialize
PROV-O today, but its internal graph should remain convertible to a provenance
model rather than collapsing evidence into an opaque profile blob.

## Discovery protocols and provider families

The lead layer is provider-agnostic. Future adapters can be added behind the
existing provider governance boundary.

Planned provider families include:

- public profile APIs (for example GitHub, GitLab, Codeforces, Bluesky, Gravatar);
- federated identity resolution using WebFinger/ActivityPub where a full
  `user@domain` identifier or profile URL is known;
- public domain/DNS/RDAP metadata;
- licensed public-web exact-match search;
- bounded public documents and operator-supplied files;
- user-authorized account/contact imports;
- optional breach-exposure checks for self-audit/authorized email addresses.

Provider terms, authentication, rate/cost limits and source risk remain separate
from lead extraction. No adapter receives permission to execute merely because a
lead exists.

## What this architecture does not mean

Recursive research is not permission to enumerate hidden accounts or infer
private identifiers.

The graph does not authorize:

- private-account bypass;
- account-recovery or login enumeration;
- credential, OTP or token collection;
- hidden KYC/government-ID acquisition;
- covert personal IP/device discovery;
- live location tracking;
- CAPTCHA/WAF evasion;
- contact with the subject without an explicit reviewed workflow;
- treating a username collision as proof of identity.

Unknown remains a valid result.

## Persistence

The recursive working graph remains ephemeral during a research run. The retained
case stores the bounded report/provenance decision record already used by private
V1.

We are deliberately not adding another persistent raw-personal-data graph yet.
That avoids duplicating sensitive data and keeps case deletion meaningful. If a
future feature truly needs a persistent graph, it requires a separate retention,
delete, migration and audit decision.

## Scaling path

The current depth and node ceilings stay unchanged while this foundation lands.
Increasing breadth is a later policy decision after provider reliability and
false-link behavior are measured.

The next implementation layers are:

1. typed lead contracts and exact-field extractor;
2. convergence integration with M1 normalization semantics;
3. deterministic frontier scheduler with per-kind/provider/cost budgets;
4. provider capability declarations (`accepts`, `emits`, cost/risk/auth);
5. graph-aware operator UI showing executed, queued, review-only, blocked and
   exhausted leads separately;
6. additional adapters behind tests and source-policy review;
7. evaluation data before any correlation-threshold or probability claims.

## Consequences

Positive:

- new providers can be added without rewriting the research loop;
- recursive expansion becomes reviewable and deterministic;
- sensitive outputs fail closed before becoming leads;
- the graph can grow in breadth without weakening M5 semantics;
- provider failures and unknowns remain first-class;
- provenance survives every hop.

Costs:

- more explicit contracts and tests are required for each source;
- some potentially useful clues require operator review instead of immediate
  execution;
- broad coverage will arrive incrementally rather than through one unrestricted
  scraper.

Those costs are intentional. A large PersonaLattice should be able to explain how
it learned something, why it followed a clue, why it stopped, and what it still
does not know.
