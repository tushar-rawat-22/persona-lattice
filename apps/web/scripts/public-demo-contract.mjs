import fs from "node:fs";
import path from "node:path";

const root = process.cwd();
const home = fs.readFileSync(path.join(root, "app/page.tsx"), "utf8");
const demo = fs.readFileSync(path.join(root, "app/demo/page.tsx"), "utf8");
const normalizedHome = home.replace(/\s+/g, " ");
const normalizedDemo = demo.replace(/\s+/g, " ");

const requiredHome = [
  "Read-only product demo",
  "Open the evidence workspace",
  "No research runs from this page",
  "Synthetic case only",
  'href="/demo"',
  'href="/admin"',
];
for (const token of requiredHome) {
  if (!normalizedHome.includes(token)) {
    throw new Error(`public home missing required demo boundary: ${token}`);
  }
}

const fixtureBackedHome = [
  'import { syntheticCase } from "./dashboard/fixture"',
  "syntheticCase.display_name",
  "syntheticCase.observations.length",
  "syntheticCase.account_candidates.length",
  "item.provenance.source_name",
  'candidate.correlation?.outcome === "contradicted"',
  "snapshotRows.map((observation)",
];
for (const token of fixtureBackedHome) {
  if (!home.includes(token)) {
    throw new Error(`public home snapshot must derive displayed case facts from the shared synthetic fixture: ${token}`);
  }
}

const forbiddenHome = [
  "fetch(",
  "/v1/cases/run",
  "/v1/files/preview",
  "run-converged",
  "type=\"file\"",
  "type=\"password\"",
  "Alex Rowan",
  "github_public_api",
  "public DNS",
];
for (const token of forbiddenHome) {
  if (home.includes(token)) throw new Error(`public home must stay non-operational and fixture-backed: ${token}`);
}

const requiredDemo = [
  "PUBLIC READ-ONLY DEMO",
  "SYNTHETIC INVESTIGATION WORKSPACE",
  "No provider requests are executed from this demo",
  "Private admin",
  "observation.provenance.source_kind",
  "observation.retrieved_at",
  "observation.expires_at",
  "correlation.policy_version",
  "correlation.evaluated_at",
  "Non-probabilistic factor assessment",
  "Supporting factors",
  "Conflicting factors",
  "Neutral / withheld factors",
  "Inspect model mechanics",
  "internal evidence-strength index / 100",
  "factor.applied_weight < 0",
  "Typed source-run states",
  'state: "executed"',
  'reason: "results_returned"',
  'state: "not_found"',
  'reason: "no_match"',
  'state: "review_required"',
  'reason: "review_gate"',
  'reason: "optional_not_configured"',
  'reason: "remote_rate_limit"',
  "They do not describe live requests",
  'role="table"',
  "Clue → evidence → operator decision",
  "compact graph view traces how a retained clue reaches a candidate",
  "identifiers.get(candidate.identifier_id)",
  "factor.observation_ids.map((observationId)",
  'factor.veto ? " → contradiction veto" : ""',
  'link.relation === "unresolved"',
  'candidate.correlation?.outcome === "insufficient_evidence"',
  "openQuestions.map((question)",
  "Claims, exceptions and open questions",
  "Private actions, public-safe states",
  'step: "Case intake"',
  'step: "Reviewed document"',
  'step: "Retained cases"',
  'step: "Delete case"',
  'step: "Session boundary"',
  "never accepts a real-person submission",
  "without a file input, upload endpoint or document retention",
  "cannot list or read private retained cases",
  "cannot mutate the fixture or call a deletion endpoint",
  "never creates an admin session",
  "Loading, failure and coverage semantics",
  'state: "Case loading"',
  'state: "Case index unavailable"',
  'state: "Research completed with limits"',
  'state: "Some source paths were not attempted"',
  'state: "No retained match from attempted sources"',
  'state: "Attempted sources completed"',
  "A failed index is not an empty workspace",
  "Missing observations from an unattempted path are a coverage limit, not negative evidence",
  "Source silence is not evidence that the subject or claim does not exist elsewhere",
  "never trigger network activity",
];
for (const token of requiredDemo) {
  if (!normalizedDemo.includes(token)) {
    throw new Error(`public demo missing required product framing, provenance, source-state, lifecycle or failure-state parity: ${token}`);
  }
}

const forbiddenDemo = [
  "fetch(",
  "/v1/cases/run",
  "/v1/cases/",
  "/v1/files/preview",
  "run-converged",
  'type="file"',
  'type="password"',
  "localStorage",
  "sessionStorage",
  "evidence score / 100",
];
for (const token of forbiddenDemo) {
  if (demo.includes(token)) throw new Error(`public demo must stay non-operational: ${token}`);
}

console.log("public demo contract passed");