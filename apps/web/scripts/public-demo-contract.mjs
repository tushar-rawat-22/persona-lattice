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
];
for (const token of requiredDemo) {
  if (!normalizedDemo.includes(token)) {
    throw new Error(`public demo missing required product framing, provenance, source-state or lifecycle parity: ${token}`);
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
];
for (const token of forbiddenDemo) {
  if (demo.includes(token)) throw new Error(`public demo must stay non-operational: ${token}`);
}

console.log("public demo contract passed");
