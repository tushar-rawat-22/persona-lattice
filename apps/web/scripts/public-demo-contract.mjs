import fs from "node:fs";
import path from "node:path";

const root = process.cwd();
const home = fs.readFileSync(path.join(root, "app/page.tsx"), "utf8");
const dashboard = fs.readFileSync(path.join(root, "app/dashboard/page.tsx"), "utf8");

const requiredHome = [
  "Read-only product demo",
  "Open the evidence workspace",
  "No research runs from this page",
  "Synthetic case only",
  'href="/dashboard"',
  'href="/admin"',
];
for (const token of requiredHome) {
  if (!home.includes(token)) throw new Error(`public home missing required demo boundary: ${token}`);
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

const requiredDashboard = [
  "PUBLIC READ-ONLY DEMO",
  "Synthetic investigation workspace",
  "No provider requests are executed from this demo",
  "Private admin",
];
for (const token of requiredDashboard) {
  if (!dashboard.includes(token)) throw new Error(`public dashboard missing required product framing: ${token}`);
}

const forbiddenDashboard = ["fetch(", "/v1/cases/run", "run-converged", 'type="file"'];
for (const token of forbiddenDashboard) {
  if (dashboard.includes(token)) throw new Error(`public dashboard must stay non-operational: ${token}`);
}

console.log("public demo contract passed");
