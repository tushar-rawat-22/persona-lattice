# Continuity

This is the public-safe handover for continuing PersonaLattice in a new ChatGPT
conversation without rebuilding context from scratch.

## How to use this file

At the start of a new project chat:

1. ask ChatGPT to read this file and the linked status/architecture documents;
2. verify the repository state rather than trusting this file blindly;
3. continue from the "Next work" section;
4. update this file after every meaningful milestone.

Do not put API keys, real investigation identifiers, private case data or
unredacted screenshots in this file.

## Project

- Name: PersonaLattice
- Repository: `tushar-rawat-22/persona-lattice`
- Visibility: public
- Local checkout: `~/persona-lattice`
- License: Apache-2.0 for original code
- Product: evidence-first identity intelligence and consented/public-source research

## Non-negotiable design rules

- AI is not evidence.
- Every factual claim must trace to source observations.
- Raw personal-data case files never enter Git.
- Provider credentials never enter Git or browser-facing contracts.
- Source/license/purpose gates exist before provider execution.
- Silent mode excludes sources with subject-contact risk.
- Uploaded document instructions are data, not execution authority.
- Document-derived candidates require human review before external research.
- Same-handle reuse across sites is not identity proof.
- Regulated employment/housing/credit/insurance decisions remain blocked.

## Architecture baseline

- Next.js web dashboard under `apps/web`
- FastAPI service under `services/api`
- SQLAlchemy evidence core under `services/api/app/evidence`
- bounded file intake/extraction under `services/api/app/uploads`
- governed provider framework under `services/api/app/providers`
- public docs live under `docs`
- `THIRD_PARTY.md` tracks license/integration boundaries

## Completed milestones

### M0 — public foundation: COMPLETE

Published:

- repository, Apache-2.0 license and source policy;
- architecture/product/roadmap documentation;
- governed case-intake API;
- consent and purpose enforcement;
- provider/contact-risk planning with no live provider execution;
- Next.js case-intake dashboard shell;
- CI for API on Python 3.11 and 3.13;
- CI for web lint, typecheck and production build.

Key M0 verification:

- governed API commit: `2dd8d12ab96819b182a9bf563d1a9d946b0b366c`
- backend warning-cleanup commit: `6fb1d305b4d198cff8a35d3a1f9daffc93a95e47`
- dashboard/CI implementation commit: `8cc62091865d71ff1177877c4e5337a463436628`
- post-merge M0 CI run: `31901840132`, conclusion `success`

### M1 — evidence core: COMPLETE

Published through PR `#4`:

- persistent `Subject`, `Identifier`, `Observation`, `Claim` and `EvidenceLink`
  SQLAlchemy models;
- database-agnostic UUIDs and SQLite development/test persistence;
- deterministic phone, email, username, URL, name and organization
  normalization outside the HTTP layer;
- source provenance, retrieval timestamps and optional expiry/freshness;
- support/contradict/unresolved evidence relationships;
- AI may originate a `Claim` but `ai` is not an allowed observation source;
- public-safe phone/email redaction helpers;
- ADR `0003-evidence-core-persistence.md`;
- synthetic-only tests.

M1 verification:

- initial evidence commit: `ac241696792553ea767677606efefc4275be5a8d`
- conservative-normalization correction: `21651e2c1ce56d57a08e569af6652ca912096778`
- final test-alignment commit: `35a6be3ba3609b1324158c62f02240b38db91f26`
- merge commit: `22d8b4c100db4861ad1890bcb224f890cd652210`
- final PR CI: `31902885290`, API 3.11 PASS, API 3.13 PASS, web PASS
- post-merge CI: `31902946010`, API 3.11 PASS, API 3.13 PASS, web PASS

During review we rejected generic case-folding for email local-parts and
usernames and rejected stripping URL fragments. Provider-specific equivalence
rules remain outside the generic core.

### M2 — safe file intake and extraction boundary: COMPLETE

Published through PR `#6`:

- PDF and UTF-8 text are the only enabled file formats;
- maximum five files, 2 MiB per file and 6 MiB combined batch;
- multipart parser/request limits plus independent streaming byte ceilings;
- untrusted filename, MIME and byte-level checks;
- private UUID-named temporary storage with restrictive permissions and SHA-256
  provenance;
- spawned extraction worker with timeout/output/PDF resource ceilings;
- raw staged bytes deleted before request completion;
- extracted content marked `untrusted_document_content`;
- deterministic identifier candidates start in `pending_human_review`;
- upload-evidence helper records extraction as an `UPLOAD` observation;
- dashboard uploads real PDF/TXT files without provider execution;
- ADR `0004-safe-file-intake.md`.

M2 verification:

- implementation commit: `4e9368ae4e7b7b66b5bca81825753a9c9d58d4c2`
- PR: `#6`
- PR CI: `31903890954`, API 3.11 PASS, API 3.13 PASS, web PASS
- merge commit: `f90b06279917cf5ddbd6bb81642e74deb3c8d5ca`
- post-merge CI: `31904034376`, API 3.11 PASS, API 3.13 PASS, web PASS
- closure commit: `1130ec3cb69c308cb281c6edf3790a7ac2ee86d9`
- closure CI: `31904139862`, API 3.11 PASS, API 3.13 PASS, web PASS

### M3 — governed provider execution framework: COMPLETE

Published through PR `#8`:

- typed/versioned provider descriptors, queries, results and error classes;
- source category, execution/review state, contact risk, allowed purposes,
  authentication mode and resource budgets in the registry;
- central authorization immediately before adapter execution;
- M2 document-derived candidates must already be human-confirmed, authorized
  and match the stored identifier kind/value;
- credentials resolve only from server-side configuration and never appear in
  the execution request contract;
- bounded retry classification with exponential delay;
- every actual adapter attempt consumes the local rate budget;
- per-provider semaphore concurrency, timeout and response-size ceilings;
- provider results become M1 `PROVIDER` observations with provider/version/source
  provenance, never automatic claims;
- public-safe provider log redaction helper;
- `synthetic_echo` is the only executable adapter through M3 and performs no
  network call;
- ADR `0005-provider-execution-boundary.md`.

M3 verification:

- initial framework commit: `3b19fde27fabdd8cdc4d366596014c528f874ec2`
- retry-budget correction: `24fd93416d22a62f87f5e8f0c267bdda38714c3e`
- explicit timeout/concurrency tests: `6fe43aaac59d14cd9b9e5a307d8aadae1350d78e`
- PR: `#8`
- final PR CI run: `31904533035`, API 3.11 PASS, API 3.13 PASS (`55 passed`), web PASS
- merge commit: `01b955637a25fda9e2efb12ffa6799e179923d6a`
- post-merge CI run: `31904600206`, API 3.11 PASS, API 3.13 PASS, web PASS
- closure commit: `c9332016494d5794cb02c4d7fd3a927f5c5872e1`
- closure CI run: `31904785271`, API 3.11 PASS, API 3.13 PASS, web PASS

M3 review deliberately caught two gaps before merge. Retries initially consumed
the local rate budget only once per high-level execution; the fix moved budget
consumption inside the actual-attempt loop. The first green implementation also
lacked direct timeout/concurrency acceptance tests; both were added and the
final PR/main runs are green.

### M4 — governed username and public-account discovery: COMPLETE

Published through PR `#10`:

- `sherlock-project==0.16.0` is the pinned published development dependency;
- the adapter reads Sherlock's packaged site data without using its live
  manifest/exclusions loader and permits only eight reviewed sites;
- parent-to-worker IPC carries only username, approved site names and timeout;
  arbitrary URL/site metadata cannot be supplied across the worker boundary;
- synchronous upstream execution runs in a child process that M3 timeout
  cancellation kills and reaps;
- M3 centrally enforces Sherlock's username-only identifier contract;
- claimed, available, unknown, illegal and WAF outcomes remain explicit;
- a claimed hit must have a valid public HTTP(S) profile URL;
- positive hits are provider observations with `account_candidate=true` and
  `identity_claim=false`;
- provider-log redaction now covers usernames;
- full page bodies are not returned from the worker or persisted;
- no provider-execution HTTP endpoint was added; Sherlock remains an internal
  development adapter rather than an unauthenticated public research surface;
- no browser opening, login/cookies, private-profile access, proxies, Tor/I2P,
  CAPTCHA/WAF bypass, follower-graph collection, account contact/recovery or
  automatic identity correlation was added;
- Maigret 0.6.3 remains non-executable.

M4 verification:

- initial implementation: `0ebe8e8e995e927c69664d617c097718a9f37a88`
- worker allowlist hardening: `7fe7b19c89c69ad0cf41a0f8ac23c1996003e466`
- published-version correction: `4a3538fc17f4b701d7d8615872bd308f34d09f07`
- duplicate-result test correction: `b42bb4dbd08bdd67a9729fbce81c4689c0f13da2`
- PR: `#10`
- final PR CI run: `31905880652`, API 3.11 PASS, API 3.13 PASS (`64 passed`), web PASS
- merge commit: `7cf43b4769da3e144e799163b4719e5cef0bf2b8`
- post-merge CI run: `31906017367`, API 3.11 PASS, API 3.13 PASS, web PASS

M4 review caught three real assumptions before closure. First, the initial
worker shape accepted caller-supplied site metadata, which was too close to an
arbitrary-URL transport; it now accepts approved site names only and reloads the
pinned package data independently. Second, the repository declared Sherlock
0.16.1 but CI proved that version was not published on the package index, so the
runtime was corrected to reviewed/published 0.16.0 rather than bypassing
reproducible installation. Third, one test expected the duplicate-result guard
while returning two rows against a one-site budget; the budget guard correctly
fired first, so the fixture was corrected without changing production behavior.

Through M4, the only real external network-capable adapter is the bounded
Sherlock development adapter, and it is not exposed through a public provider
execution endpoint. No real case data, provider credential, live AI, production
authentication or report export has been introduced.

## Next work

**M5 — explainable evidence correlation engine (Issue `#11`).**

M5 is deliberately deterministic before it is probabilistic:

- correlate existing identifiers/observations only; no new provider calls;
- keep correlation results separate from factual Claims;
- use versioned factor weights, contradiction/veto rules and source-independence
  groups;
- make same-handle-only evidence non-decisive;
- expose every contributing observation and reason;
- test stale evidence, duplicated mirrors, collisions and contradictions with
  synthetic/adversarial fixtures;
- do not describe a heuristic score as a calibrated identity probability.

The older roadmap wording around "calibrated confidence bands" was too strong.
Calibration requires a lawful, reviewed labeled benchmark and empirical
validation; until that exists, M5 will expose evidence-strength/triage outcomes
with an explicit uncalibrated status.

## Bootstrap recovery record

The initial M0 bootstrap was interrupted twice before backend publication:

1. macOS resolved `python3` to Python 3.9.6 while the API requires 3.11+;
2. a broad Ruff range installed Ruff 0.16 and changed the lint contract.

Recovery decision:

- keep Python >=3.11 and Homebrew Python 3.13 locally;
- pin Ruff 0.15.15 and define the lint rule set explicitly;
- publish backend code only after lint, compile, tests and smoke verification.

## Backend warning cleanup

The baseline uses HTTPX2 2.9.0 for Starlette TestClient, the current 422 status
constant and treats Starlette deprecation warnings as test failures.

## Update discipline

For every milestone update:

- current repository/branch;
- latest meaningful commits;
- tests and verification run;
- what changed;
- what did not change;
- unresolved risks;
- next authorized work.

The point is continuity, not marketing copy.
