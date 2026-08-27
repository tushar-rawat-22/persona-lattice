import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const appRoot = path.resolve(here, "..");
const css = await readFile(path.join(appRoot, "app", "globals.css"), "utf8");
const adminPage = await readFile(path.join(appRoot, "app", "admin", "page.tsx"), "utf8");
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
  ".workspaceTabs",
  ".workspaceTab.active",
  ".compactTable",
  ".tableScroll",
  ".caseContextBar",
  ".workspace.caseActive",
  ".intakeDrawer",
  ".researchWorkbench.activeResearch",
  ".evidenceAssessmentList",
  ".evidenceFactors",
  ".workspaceBoundary",
  ".workspace.caseActive, .publicGrid { grid-template-columns: 1fr; }",
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
  "Investigation workspace",
  "Active investigation",
  "Start another case",
  "Stored cases",
  "Overview",
  "Accounts & pivots",
  "Sources",
  "Graph",
  "Raw",
  "M5 evidence-strength triage",
  "Evidence pivots",
  "Source execution",
  "Raw retained JSON",
  "Canonical pivot provenance could not be resolved safely.",
  "Source execution state is unavailable for this historical case.",
  'role="tablist"',
  'role="tab"',
  'role="tabpanel"',
  'aria-selected={activeView === view}',
  'tabIndex={activeView === view ? 0 : -1}',
  'event.key === "ArrowRight"',
  'event.key === "ArrowLeft"',
  'event.key === "Home"',
  'event.key === "End"',
  'className="compactTable sourceTable"',
  'className="compactTable m5Table"',
  'className="evidenceAssessment"',
  'className="evidenceFactors"',
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
assert.ok(
  research.indexOf('overview: "Overview"') < research.indexOf('raw: "Raw"'),
  "operator workspace must keep summary-first task ordering",
);
assert.ok(
  research.includes("not an identity probability") && research.includes("identity_probability: null"),
  "M5 must remain explicitly non-probabilistic in the operator workspace",
);
assert.ok(
  adminPage.includes('className={caseWorkspaceActive ? "workspace caseActive" : "workspace"}') &&
    adminPage.includes('className="panel intakeDrawer"') &&
    adminPage.includes("onActiveCaseChange={handleActiveCaseChange}") &&
    adminPage.includes("(!caseWorkspaceActive || result)"),
  "active-case selection must collapse intake and promote the investigation workspace",
);
assert.ok(
  research.includes("onActiveCaseChange?.(Boolean(activeCase))") &&
    research.includes("setLauncherOpen(false)") &&
    research.includes("Inspect {factorRows.length} retained factor"),
  "case-first layout and progressive M5 factor disclosure must remain wired to real case state",
);
assert.ok(
  adminPage.includes('new FormData(event.currentTarget)') &&
    adminPage.includes('formData.get("username")') &&
    adminPage.includes('formData.get("password")') &&
    adminPage.includes('name="username"') &&
    adminPage.includes('name="password"'),
  "admin login must submit the browser form values instead of relying on delayed controlled state",
);

console.log("operator workspace contract: PASS");
