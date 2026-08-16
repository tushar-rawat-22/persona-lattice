# Continuity

This is the public-safe continuation record for PersonaLattice. Read it together
with `docs/ROADMAP.md`, `docs/V2_SOURCE_EXPANSION_PLAN.md` and the ADRs, then
verify GitHub before changing anything. Do not trust commit/state claims blindly.

Never put API keys, real research identifiers, private retained-case data,
password hashes, session material or unredacted investigation screenshots here.

## Project

- Repository: `tushar-rawat-22/persona-lattice`
- Local checkout: `~/persona-lattice`
- Default branch: `main`
- License: Apache-2.0 for original code
- Product: private evidence-first public/authorized research workbench
- Operating model: one authenticated operator; public route is demo/preview only

## Non-negotiable evidence semantics

These are architecture rules, not UI wording:

- source Observations, factual Claims and correlation results stay separate;
- every factual conclusion must preserve provenance;
- a discovered clue is a research lead, not proof of identity;
- same-handle reuse alone is weak evidence and never identity proof;
- M5 is deterministic evidence-strength triage, not identity probability;
- `calibration_status` remains `uncalibrated`;
- `is_identity_claim` remains `false`;
- contradictions/vetoes and stale evidence remain visible;
- no AI/ML/embedding/biometric identity decision is in the correlation path;
- no provider expansion is authorized by an M5 score;
- unknown/not-found/unavailable are legitimate outcomes and must not be guessed
  into positive evidence.

## Non-negotiable security/privacy boundary

PersonaLattice may expand attributable public information and explicitly
authorized data. It does not add:

- private-account bypass;
- login/account-recovery enumeration;
- credential, password, OTP, session or token collection;
- CAPTCHA/WAF/proxy/Tor evasion;
- hidden KYC or government-ID acquisition;
- covert personal/device IP discovery;
- live location tracking;
- covert subject contact;
- regulated employment/housing/credit/insurance eligibility decisions.

The recursive V2 lead extractor also blocks government-ID, credential/token and
personal/device-IP field classes from entering the lead graph. It can retain only
the blocked field name for audit/debugging, never the blocked value.

## Architecture baseline

- Next.js operator/public UI: `apps/web`
- FastAPI API: `services/api`
- M1 evidence/persistence/normalization: `services/api/app/evidence`
- M2 bounded file intake: `services/api/app/uploads`
- M3 governed provider framework: `services/api/app/providers`
- M5 deterministic correlation: `services/api/app/correlation`
- V1/V2 convergence: `services/api/app/convergence.py`
- V2 typed leads/frontier/source planning: `services/api/app/intelligence`
- private retained cases: `services/api/app/cases.py`
- audit/auth/session boundaries: `services/api/app/audit.py`, admin auth/session
  modules
- V2 source expansion plan: `docs/V2_SOURCE_EXPANSION_PLAN.md`
- V2 ADRs: `0010`, `0011`, `0012`

## Completed foundation milestones

M0 through M6 are complete and remain historical foundations:

- M0: repository/product/API/web/CI foundation;
- M1: persistent evidence model, conservative normalization and provenance;
- M2: bounded file intake/extraction and human-review candidates;
- M3: governed provider contracts, purpose/consent/credential/rate/resource gates;
- M4: reviewed bounded Sherlock username discovery;
- M5: deterministic explainable evidence correlation;
- M6: local synthetic evidence-intelligence dashboard.

Important M5 closure commit: `6555ae8ecee3aff8ef4a2ce191d055b17902d63f`.
M6 toolchain/lockfile closure was published through PR `#14`.

## Private V1 — implemented and locally accepted

The repository now also contains the private one-admin V1 product:

- one deployment-configured admin identity; no public registration/teams;
- Argon2 password verification and opaque HttpOnly session cookie;
- logout/revocation, CSRF protection and same-origin `/api` proxy;
- public root contains only product/demo content;
- private `/admin` console performs real authorized intake/research;
- retained cases, deletion/expiry and privacy-safe audit events;
- GitHub/GitLab/Codeforces public-profile enrichment;
- reviewed Sherlock account-candidate discovery;
- phone numbering-plan/carrier/region/time-zone metadata;
- exact public-email/public-web paths where configured and allowed;
- ephemeral canonical evidence graph feeding M5 before the bounded retained report
  is stored.

The operator has successfully run the product locally through a public HTTPS
ngrok tunnel with the Next.js service on port 3000 and the FastAPI service bound
to local port 8000. Login and authenticated case reads returned HTTP 200 during
manual acceptance. The tunnel is an operational preview, not durable hosting.
Do not commit its ephemeral URL or any test identifier.

## V2 recursive evidence graph foundation — COMPLETE

The V2 goal is:

> Start with the smallest defensible clue and expand outward through attributable
> public or explicitly authorized evidence. Every clue becomes a typed lead;
> every lead preserves its source; only policy-approved leads become another
> automated query.

### PR #20 — typed lead graph foundation

Merge commit: `e66944259c545cdfe8e4020312357b92a42911ba`.

Implemented:

- `LeadKind`: username, email, phone, URL, domain, name, organization, location;
- dispositions: `auto_pivot`, `review_required`, `display_only`, `blocked`;
- exact-field allowlisted lead extraction;
- M1 normalization reused as the generic normalization authority;
- newly discovered phone numbers default to review-required rather than silent
  fan-out;
- contextual name/org/location default to display-only;
- government IDs, credentials/tokens and personal/device IP fields fail closed;
- deterministic frontier infrastructure with reservations and budgets;
- ADR `0010-recursive-evidence-lead-graph.md`;
- `docs/V2_SOURCE_EXPANSION_PLAN.md`.

A concrete bug was fixed here: the old convergence node key generically
case-folded identifiers even though M1 intentionally preserves generic username
case and email local-part case. V2 now uses M1-consistent comparison keys.

### PR #21 — deterministic frontier orchestration

Merge commit: `2a69224e53ea1912879032548a38f017bfcafb6a`.
Post-merge CI run `31974590505`: success.

Implemented:

- `LeadFrontier` is the run-local admission authority;
- capacity is reserved before provider execution so future concurrency cannot
  oversubscribe node/edge/kind/fan-out budgets;
- final lead outcomes include `admitted`, `provider_failed`, `duplicate`,
  `review_required`, `display_only` and reason-coded budget stops;
- failed execution releases capacity but the same lead is not retried repeatedly
  in one run;
- duplicate clue origins remain visible even though canonical provider execution
  happens once;
- lead decisions are retained in additive `lead_graph` report state;
- current private-V1 depth/node behavior remains compatible;
- ADR `0011-deterministic-frontier-orchestration.md`.

Review caught and fixed two subtle flaws before closure: reservation capacity had
to count against future concurrent budgets, and duplicate detection had to take
precedence over depth-limit reporting so known clues do not falsely mark a run as
truncated.

### PR #22 — source capability registry and planner

Merge commit: `b1192fd15d73c144faba6279559db3e2b6ae2980`.
Post-merge CI run `31974993479`: API 3.11 PASS, API 3.13 PASS, web PASS,
deployment-image PASS.

Implemented:

- static source capability catalog separated from execution authority;
- accepted/emitted lead kinds, lifecycle status, source mode, cost class,
  credential class, source-policy review state and recursive eligibility;
- non-executing source planner with `active`, `optional`, `deferred`, `planned`
  and budget-excluded buckets;
- current zero-spend-capable sources separated from metered optional search;
- existing deferred/manual/reference provider-registry candidates represented
  without making them executable;
- planned integration targets for Bluesky, Gravatar, WebFinger/ActivityPub,
  RDAP and user-authorized Google People imports;
- source catalog/provider-registry consistency tests;
- ADR `0012-source-capability-catalog.md`.

A catalog match is never permission to call a source. Planned/review/manual/
reference entries remain non-recursive by construction until an adapter and
current source-policy review exist.

## Current research graph

The intended V2 flow is now:

```text
operator seed
  -> M1 normalization
  -> source capability plan
  -> live source/provider authorization
  -> bounded source execution
  -> provenance-bearing Observation
  -> exact-field lead extraction
  -> lead disposition
  -> deterministic frontier admission
  -> next research node
  -> repeat within budgets
  -> ephemeral canonical M1 graph
  -> M5 evidence-strength triage
  -> bounded retained report/provenance record
```

The working recursive graph stays ephemeral during a run. PersonaLattice does
not yet create a second persistent raw-personal-data graph, so case deletion does
not leave a hidden duplicate evidence store.

## Current limits that are deliberate

- convergence maximum depth remains 2;
- convergence maximum nodes remains 12;
- planned source adapters do not execute yet;
- contextual names, organizations and locations do not autonomously fan out;
- newly discovered phone numbers require review;
- public-search snippets do not automatically become identifier leads;
- no identity probability is displayed or stored;
- no API/source is claimed to provide universal account membership or hidden
  personal identifiers.

Do not raise graph breadth/depth simply to make demos look richer. First measure
wrong-pivot, duplicate, provider-failure, graph-growth and source-reliability
rates on synthetic/consented fixtures.

## Next work

**V2 source-adapter activation, one reviewed source family at a time.**

Order of work:

1. add adapter/runtime consistency so a catalogued source cannot execute unless
   its live adapter, catalog capability and source-policy gate agree;
2. build synthetic fixture adapters/tests for the planned source contract before
   real network calls;
3. activate low/no-spend public sources in this order after fresh official-source
   review: Bluesky public profiles, Gravatar public profiles, WebFinger/
   ActivityPub federation resolution, RDAP domain metadata;
4. expose source-plan/lead states in the private graph UI: executed, not-found,
   queued, review-required, display-only, blocked, unavailable, budget-stopped;
5. only after the graph/source layer is measured, proceed to M10 labelled
   evaluation/calibration work.

Paid enrichment is not the next step. The architecture should first make adding a
source boring, bounded and reviewable.

## Update discipline

After every meaningful block record:

- verified main HEAD and relevant branch/PR;
- CI/test state;
- what changed;
- what explicitly did not change;
- assumptions challenged/fixed;
- unresolved risks;
- next authorized work.

The point is continuity, not marketing copy.
