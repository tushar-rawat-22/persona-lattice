import fs from "node:fs";
import path from "node:path";

const root = process.cwd();
const demo = fs.readFileSync(path.join(root, "app/demo/page.tsx"), "utf8");
const simulation = fs.readFileSync(
  path.join(root, "app/demo/retained-case-navigation-simulation.tsx"),
  "utf8",
);
const normalized = simulation.replace(/\s+/g, " ");

const required = [
  "RETAINED CASES / SAFE SIMULATION",
  "Search, filter and switch synthetic cases",
  "browser-memory fixture only",
  'type="search"',
  "All kinds",
  "Current workspace context",
  "Active synthetic case is hidden by filters.",
  "Show active case",
  "No synthetic cases match these filters.",
  "This is an empty filter result, not a failed case index.",
  "Delete retained case",
  "Destructive case mutation is intentionally disabled in the public observer.",
  "aria-pressed={active}",
  'setQuery("")',
  'setKind("all")',
];
for (const token of required) {
  if (!normalized.includes(token)) {
    throw new Error(`public retained-case simulation missing required parity token: ${token}`);
  }
}

const forbidden = [
  "fetch(",
  "/v1/",
  "localStorage",
  "sessionStorage",
  "document.cookie",
  'type="password"',
  "DELETE",
];
for (const token of forbidden) {
  if (simulation.includes(token)) {
    throw new Error(`public retained-case simulation must stay local-only and non-operational: ${token}`);
  }
}

if (!demo.includes('import { RetainedCaseNavigationSimulation } from "./retained-case-navigation-simulation";')) {
  throw new Error("public demo must import retained-case navigation simulation");
}
if (!demo.includes("<RetainedCaseNavigationSimulation />")) {
  throw new Error("public demo must mount retained-case navigation simulation in the evidence workspace");
}

console.log("public retained-case navigation contract passed");
