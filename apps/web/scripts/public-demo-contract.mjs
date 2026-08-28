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

const forbiddenHome = [
  "fetch(",
  "/v1/cases/run",
  "/v1/files/preview",
  "run-converged",
  "type=\"file\"",
  "type=\"password\"",
];
for (const token of forbiddenHome) {
  if (home.includes(token)) throw new Error(`public home must stay non-operational: ${token}`);
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
];
for (const token of requiredDemo) {
  if (!normalizedDemo.includes(token)) {
    throw new Error(`public demo missing required product framing or provenance field: ${token}`);
  }
}

const forbiddenDemo = ["fetch(", "/v1/cases/run", "run-converged", 'type="file"', 'type="password"'];
for (const token of forbiddenDemo) {
  if (demo.includes(token)) throw new Error(`public demo must stay non-operational: ${token}`);
}

console.log("public demo contract passed");
