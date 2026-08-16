# PersonaLattice private V1 status

This file is the concise closure contract for the private-admin V1. It contains
no credentials, real investigation identifiers or private case data.

## Product boundary

PersonaLattice is a public-hosted product shell with one private operator/admin
account. Unauthenticated users may see synthetic/demo UI only. Real research
intake, provider execution, retained cases, evidence, audit records and reports
require the authenticated admin session.

Blurred presentation is not access control: the backend must not send real case
payloads to an unauthenticated browser.

## Supported starting inputs

- username / social handle;
- phone number;
- email address;
- public HTTP(S) profile or website URL;
- bounded PDF, UTF-8 text, JPEG and PNG upload intake.

## Research paths

### Username

- fixed reviewed Sherlock public-account subset;
- GitHub public profile API;
- GitLab public user API;
- Codeforces public user API;
- optional exact-match Brave public-web index lookup.

### Email

- canonical normalization/domain extraction;
- exact GitLab public-email match when that email is explicitly exposed;
- optional exact-match Brave public-web index lookup.

### Phone

- libphonenumber numbering-plan validity/region/carrier/timezone metadata;
- optional exact-match Brave public-web index lookup;
- no claim that numbering metadata identifies the subscriber.

### URL

- canonical URL components;
- globally reachable DNS infrastructure addresses only;
- optional exact-match Brave public-web index lookup;
- infrastructure IPs are never labelled as a person's device IP or current
  physical location.

## Convergence

The V1 convergence engine performs bounded public-evidence expansion:

- maximum depth: 2;
- maximum research nodes: 12;
- automatic pivots: reviewed public email, username and website fields only;
- every pivot retains the source and source locator that caused the expansion;
- duplicate pivots are suppressed before provider execution;
- provider failures are isolated into warnings rather than corrupting the whole
  case;
- locations, organizations, network/IP identifiers, LinkedIn and Discord fields
  are display evidence only and are not autonomous pivots.

A pivot means "research this attributable public field," not "this field belongs
to the same person."

## Canonical M5 integration

Live converged evidence is admitted to an ephemeral canonical evidence graph and
passed through the existing deterministic M5 correlation engine.

The following invariants remain mandatory:

- score is evidence-strength triage, not identity probability;
- `calibration_status=uncalibrated`;
- `is_identity_claim=false`;
- same username remains weak evidence;
- an exact original email seed publicly exposed by a candidate may create the
  reviewed exact-identifier factor;
- a public email discovered from the candidate itself cannot bootstrap its own
  strong identity factor;
- source independence, stale evidence and contradiction/veto semantics remain
  M5 concerns rather than UI guesses.

The canonical graph used for live evaluation is in-memory/ephemeral. The retained
private case stores the decision record and provenance, avoiding a hidden second
persistent personal-data store after case deletion.

## Private data lifecycle

- retained cases default to 30 days;
- expired cases can be purged;
- individual cases can be deleted;
- all retained cases can be deleted;
- operational audit events are stored separately but deliberately do not copy
  research seed values, provider payloads, passwords, bearer secrets or CSRF
  tokens;
- secrets are supplied through deployment configuration and never committed.

## Deployment

`render.yaml` defines:

- `personalattice-api` as the FastAPI/Docker service with a persistent case disk;
- `personalattice-web` as the public Next.js service;
- same-origin browser requests under `/api` proxy to the API using Render's
  service `hostport` reference;
- admin username and Argon2 password hash as dashboard-provided secrets;
- optional `BRAVE_SEARCH_API_KEY` as a dashboard-provided secret.

The repository can be deployed without the Brave key; licensed broad public-web
index discovery is then omitted while the other research paths continue to work.

## Explicit non-features

V1 does not perform:

- unauthorized system access or extraction;
- private-account/login bypass;
- credential, OTP or account-recovery attacks;
- CAPTCHA/WAF evasion;
- covert subject contact;
- tracking-link IP collection, covert device-IP discovery or deanonymization;
- Internet-scale face recognition/reverse-face identification;
- regulated employment/housing/credit/insurance eligibility decisions.

## Definition of V1 implementation complete

V1 code can be merged when all of these are true:

1. API Python 3.11 passes;
2. API Python 3.13 passes;
3. Ruff passes;
4. web `npm ci`, lint, typecheck and production build pass;
5. public unauthenticated UI remains synthetic/demo-only;
6. real-case endpoints remain admin protected;
7. convergence and M5 synthetic acceptance tests pass;
8. retention/delete/audit tests pass;
9. deployment Blueprint contains both web and API services without hardcoded
   credentials.

Actual Internet deployment still requires the repository owner to connect the
Render account and enter deployment secrets. That account-bound action is not a
code-completeness gap.
