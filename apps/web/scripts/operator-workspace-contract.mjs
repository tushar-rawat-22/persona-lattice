import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const appRoot = path.resolve(here, "..");
const css = await readFile(path.join(appRoot, "app", "globals.css"), "utf8");
const research = await readFile(path.join(appRoot, "app", "admin", "quick-research.tsx"), "utf8");

const requiredCss = [
  "font-family: -apple-system, BlinkMacSystemFont",
  ".hero h1",
  "font-size: 18px",
  ".hero .lede { display: none; }",
  "button:focus-visible",
  ".recentCases",
  "grid-template-columns: 220px minmax(0, 1fr)",
  "overflow: auto",
  "scrollbar-gutter: stable",
  "box-shadow: none",
];

for (const token of requiredCss) {
  assert.ok(css.includes(token), `operator workspace CSS is missing required contract token: ${token}`);
}

const forbiddenCss = [
  "radial-gradient(",
  "linear-gradient(",
  "glassmorphism",
];

for (const token of forbiddenCss) {
  assert.ok(!css.includes(token), `operator workspace CSS reintroduced forbidden decorative treatment: ${token}`);
}

const requiredResearch = [
  "Converged live research",
  "Stored cases",
  "M5 evidence-strength triage",
  "Evidence pivots",
  "Source execution",
  "Raw retained JSON",
  "Canonical pivot provenance could not be resolved safely.",
  "Source execution state is unavailable for this historical case.",
];

for (const token of requiredResearch) {
  assert.ok(research.includes(token), `operator workspace lost required evidence/provenance affordance: ${token}`);
}

assert.ok(
  research.includes("<details>") && research.includes("<summary>Raw retained JSON</summary>"),
  "raw provider payload must remain progressively disclosed",
);
assert.ok(
  research.includes("SourceRunSummary") && research.includes("resolveEdgeProvenance"),
  "source execution and canonical provenance context must remain available alongside raw provider detail",
);

console.log("operator workspace contract: PASS");
