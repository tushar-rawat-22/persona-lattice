# PersonaLattice V2 source expansion plan

## Product objective

Start with the smallest defensible clue and expand outward through attributable
public or explicitly authorized evidence. Every new clue becomes a typed lead;
every lead keeps the source that produced it; only policy-approved leads become
another automated query.

The target is not a single "person profile" assembled from guesses. The target is
a research graph that answers:

- what was observed;
- where it was observed;
- what new lead that observation created;
- whether the lead was executed, queued for review, display-only or blocked;
- which sources agree or contradict one another;
- what remains unknown.

## Architecture before APIs

Provider expansion does not start by adding HTTP calls. Each source must fit the
same pipeline:

```
seed
  -> M1 normalization
  -> provider eligibility/purpose/consent gate
  -> bounded provider execution
  -> provenance-bearing observation
  -> exact-field lead extraction
  -> lead disposition
  -> bounded recursive frontier
  -> M5 evidence-strength triage
  -> retained report/provenance record
```

The lead layer is deliberately provider-agnostic. A provider may expose useful
fields without automatically receiving permission to trigger more research.

## Provider admission contract

No provider becomes executable until its adapter has a reviewed declaration for:

1. source owner and official documentation;
2. terms/license status for the intended use;
3. supported seed kinds;
4. exact public/authorized fields that may be returned;
5. exact fields allowed to emit new leads;
6. contact/notification risk to the subject;
7. authentication and server-side secret handling;
8. request, concurrency, timeout and response-size limits;
9. free/metered cost class;
10. deterministic fixture tests for success, not-found, malformed, rate-limited
    and provider-down responses;
11. source-locator/provenance requirements;
12. retention and redaction behavior.

"It has an API" is not enough.

## Source families

### A. Public profile APIs

Purpose: enrich a known public username/handle with fields the profile owner or
platform exposes publicly.

Current:

- GitHub
- GitLab
- Codeforces
- reviewed Sherlock site subset

Next candidates:

- Bluesky profile lookup by DID or handle;
- Gravatar profile lookup by email hash/profile slug;
- other official public-profile APIs after terms review.

Expected emitted leads:

- public username/handle;
- explicitly public email;
- public profile/website URL;
- verified account URL where the provider states it is verified.

Display-only context may include public display name, company, bio and location.

### B. Federated social identity

Purpose: resolve a known federated handle such as `user@domain` or an explicit
profile URL without guessing server-specific URL structures.

Standards:

- WebFinger (RFC 7033) for resolving an `acct:` resource to canonical profile/
  actor links;
- ActivityPub for public actor/profile representations where supported.

This family is useful because the domain is part of the identifier. `alice` on
one server is not assumed to be `alice` on another server.

### C. Email-to-public-profile enrichment

Purpose: use an already-known/authorized email address to find profiles that
explicitly map that email to public profile data.

Candidate:

- Gravatar public profile API using the SHA-256 email identifier.

Potential output includes display name, profile URL, location, company and
verified public accounts when the user published them.

This is not a universal account-existence checker. Absence is reported as
unknown/not found, not proof that the email has no account elsewhere.

### D. Domain and public infrastructure intelligence

Purpose: turn a public website/domain lead into context about the resource that
published it.

Standards/sources:

- DNS metadata;
- RDAP for domain/registry registration data where the registry exposes it;
- public website metadata and contact pages through a separately reviewed fetch
  boundary.

Public hostname infrastructure addresses may be evidence about the website.
They are never treated as the subject's personal/device IP address.

### E. Public-web exact-match discovery

Purpose: find pages that visibly publish the exact seed identifier.

Current optional path:

- licensed Brave public-web exact-match search.

Rules:

- exact identifier queries only unless a future search policy explicitly expands
  scope;
- search snippets are observations, not identity proof;
- page fetching is a separate capability with independent SSRF/content/size
  controls;
- result URLs must remain attached to every emitted lead.

### F. User-authorized account/contact imports

Purpose: enrich a self-audit or consented case using data the operator is
explicitly authorized to access.

Example:

- Google People API for the authenticated user's own contacts/profile data.

This family is different from public OSINT. Authorization scope, token storage,
revocation and audit must be explicit.

### G. Documents and operator-supplied evidence

Purpose: extract candidate clues from resumes, public reports, portfolios and
other files the operator is allowed to process.

Current bounded PDF/TXT/JPEG/PNG intake remains the entry point.

Future work:

- richer deterministic entity extraction;
- per-candidate review state;
- source-page/offset provenance;
- explicit promotion from document candidate to research lead.

Uploaded text remains untrusted data and never becomes execution authority.

### H. Breach exposure

Purpose: self-audit/authorized notification that a known email appears in a
published breach corpus from a legitimate provider.

This is a separate source class because breach data has higher sensitivity and
stricter terms. The output must be breach exposure metadata, not leaked passwords,
secrets or a mechanism for account takeover.

## Platform categories we do not fake

A large product should not pretend every consumer platform has a lawful,
reliable public lookup API.

For gaming, social, professional and messaging services:

- use official/public APIs when they expose the required field;
- use public profile URLs supplied by another attributable source;
- mark unsupported sources as `review_required`, `manual_only` or unavailable;
- do not replace a missing API with login probing, account recovery, private
  scraping, CAPTCHA/WAF evasion or credential use.

A provider returning "unknown" is better than a fabricated claim of total
coverage.

## Frontier policy

The future scheduler should be deterministic and budgeted along independent axes:

- maximum graph depth;
- maximum total nodes/edges;
- maximum children emitted per source observation;
- per-lead-kind budgets;
- per-provider request budgets;
- per-provider concurrency/timeouts;
- per-run cost ceiling;
- duplicate/cycle suppression;
- manual-review queue for higher-sensitivity leads.

Priority should favor exact attributable identifiers over contextual attributes.
A useful default order is:

1. verified/explicit public email or profile URL;
2. exact public username/handle;
3. domain derived from an attributable public URL;
4. review-approved phone lead;
5. contextual name/organization/location for display and analyst review only.

## Graph/report UX

The operator view should separate state, not just list providers:

- **executed** — source was actually queried;
- **not found** — provider executed and returned a negative result;
- **queued** — eligible lead waiting within the frontier;
- **review required** — visible clue that needs operator approval before research;
- **display only** — useful context that is intentionally not queried;
- **blocked** — field class is outside the recursive boundary;
- **unavailable** — provider failed/rate-limited/was not configured;
- **budget stopped** — valid work existed but the run ceiling stopped expansion.

Every edge should show its source locator and reason. M5 results remain a separate
evidence-strength layer and never become identity probability without future
calibration evidence.

## Build order

### Foundation — now

- typed lead contract;
- exact-field extractor;
- sensitive-field fail-closed behavior;
- convergence integration;
- case-sensitive M1 normalization regression tests;
- ADR 0010.

### Frontier scheduler

- deterministic priority queue;
- node/edge/per-kind/per-provider/cost budgets;
- review queue;
- cycle suppression and reason-coded stop states;
- graph snapshot contract for UI.

### Capability registry

- provider `accepts` and `emits` declarations;
- source terms/review state;
- cost class and credentials;
- provider health/reliability metrics;
- no adapter execution unless capability declaration and policy agree.

### Zero/low-cost public adapters

After the infrastructure is green, evaluate in this order:

1. Bluesky public profiles;
2. WebFinger/ActivityPub resolution;
3. Gravatar public profile lookup;
4. RDAP/domain metadata;
5. additional public profile APIs with clear terms.

### Operator-authorized sources

Add only after token lifecycle/audit is defined:

- Google contacts/profile imports;
- other user-owned account exports or APIs.

### Evaluation

Before increasing recursion limits or changing M5 thresholds:

- create synthetic/consented labelled graph fixtures;
- measure wrong-pivot rate, duplicate rate and source failure rate;
- measure graph growth and cost per seed;
- run factor ablations;
- keep identity probability disabled unless calibration evidence supports it.

## Success criteria

V2 is successful when a single small clue can generate a broad, inspectable graph
of defensible leads while the operator can answer, for every hop:

> What source produced this clue, why was it allowed to become a lead, what did we
> do with it, and how certain are we about the relationship?

Breadth without that answer is not intelligence; it is an unreviewable data dump.
