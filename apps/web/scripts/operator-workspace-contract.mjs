import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const appRoot = path.resolve(here, "..");
const css = await readFile(path.join(appRoot, "app", "globals.css"), "utf8");
const adminPage = await readFile(path.join(appRoot, "app", "admin", "page.tsx"), "utf8");
const research = await readFile(path.join(appRoot, "app", "admin", "quick-research.tsx"), "utf8");
const caseNavigation = await readFile(path.join(appRoot, "app", "admin", "case-navigation.tsx"), "utf8");
const provenanceDisclosure = await readFile(path.join(appRoot, "app", "admin", "provenance-disclosure.tsx"), "utf8");

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
  "Overview",
  "Accounts & pivots",
  "Sources",
  "Graph",
  "Raw",
  "Corroborated evidence",
  "Conflicts & uncertainty",
  "Open questions",
  'className="decisionSurface reportSection"',
  "deriveCorroboratedEvidence",
  "deriveUncertaintyItems",
  "deriveOpenQuestions",
  "No retained observation is independently corroborated by two distinct sources yet.",
  "M5 evidence-strength triage",
  "Evidence pivots",
  "Source execution",
  "Raw retained JSON",
  "Canonical pivot provenance could not be resolved safely.",
  "Source execution state is unavailable for this historical case.",
  "Evidence path",
  "Retained evidence sequence",
  "This case format does not retain per-observation timestamps",
  "Inspect raw topology",
  "nodeByKey",
  "observationSequence",
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

const requiredCaseNavigation = [
  "Search retained cases",
  "Filter by kind",
  "Sort results",
  "filterAndSortLoadedCases",
  "retainedCaseSearchPath",
  "caseNavigationControls",
  "caseNavigationFooter",
  'className="caseActions"',
  "Current workspace context",
  "CASE {activeCase.id.slice(0, 8)}",
  "Delete this case",
  "Delete all retained cases",
  "new Date(item.created_at).toLocaleString()",
  "left.id.localeCompare(right.id)",
  "No retained cases match the current search and kind filter.",
];

for (const token of requiredCaseNavigation) {
  assert.ok(caseNavigation.includes(token), `retained-case navigation lost required behavior: ${token}`);
}
assert.ok(
  caseNavigation.includes("kind !== \"all\" && item.seed_kind !== kind") &&
    caseNavigation.includes("candidate.toLocaleLowerCase().includes(needle)") &&
    caseNavigation.includes('sortOrder === "newest" ? -createdDelta : createdDelta'),
  "retained-case navigation must preserve deterministic local filtering/sorting for loaded or returned metadata",
);
assert.ok(
  caseNavigation.includes('aria-current={activeCaseId === item.id ? "true" : undefined}') &&
    caseNavigation.includes("Search retained case metadata without loading retained report payloads.") &&
    caseNavigation.includes('credentials: "include"') &&
    caseNavigation.includes('response.headers.get("X-PersonaLattice-Next-Cursor")'),
  "retained-case navigation must expose active state and use bounded authenticated server metadata search",
);
assert.ok(
  caseNavigation.includes("[...cases, ...remoteCases].find((item) => item.id === activeCaseId)") &&
    caseNavigation.includes("KIND_LABELS[activeCase.seed_kind]") &&
    caseNavigation.includes("activeCase.seed_value") &&
    caseNavigation.includes("caseRetentionStatus(activeCase.expires_at)"),
  "retained-case navigation must pin exact active-case context and retention truth above mutable filters",
);
assert.ok(
  research.includes('import { CaseNavigation } from "./case-navigation";') &&
    research.includes("<CaseNavigation") &&
    research.includes("cases={recentCases}") &&
    research.includes("activeCaseId={activeCase?.id}") &&
    research.includes("hasMore={Boolean(nextCaseCursor)}") &&
    research.includes("loadingMore={loadingOlderCases}") &&
    research.includes("onOpenCase={openCase}") &&
    research.includes("onLoadMore={loadOlderCases}") &&
    research.includes("onDeleteCase={deleteCase}") &&
    research.includes("onDeleteAll={deleteAllCases}"),
  "retained-case navigation must be wired to the real retained-case state and lifecycle handlers",
);
assert.ok(
  !research.includes('<div className="recentCases">') &&
    !research.includes('onClick={() => deleteCase(item.id)}>Delete</button>'),
  "legacy retained-case markup must not remain alongside the navigation component",
);

const requiredProvenanceDisclosure = [
  'className="provenanceDisclosure"',
  'className="provenanceList"',
  "Inspect provenance",
  "Open canonical source",
  "Canonical locator is not a safe public web URL.",
  "record.sourceState",
  "record.leadKind",
  'target="_blank"',
  'rel="noopener noreferrer"',
];
for (const token of requiredProvenanceDisclosure) {
  assert.ok(provenanceDisclosure.includes(token), `provenance disclosure lost required operator context: ${token}`);
}
assert.ok(
  provenanceDisclosure.includes('["http:", "https:"].includes(parsed.protocol)') &&
    provenanceDisclosure.includes("parsed.username || parsed.password || !parsed.hostname") &&
    provenanceDisclosure.includes("record.source === candidate.source") === false,
  "provenance disclosure must fail closed for unsafe locators and avoid unsafe navigation",
);
assert.ok(
  provenanceDisclosure.includes("candidate.source === record.source") &&
    provenanceDisclosure.includes("candidate.sourceLocator === record.sourceLocator"),
  "provenance disclosure must deduplicate exact retained source/locator pairs without collapsing distinct evidence",
);
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
  research.includes("sources.size >= 2") &&
    research.includes('!["executed", "not_found"].includes(record.state)') &&
    research.includes("factor.veto || factor.applied_weight < 0"),
  "decision surface must derive corroboration, unresolved source gaps and conflicting evidence from retained case data",
);
assert.ok(
  !research.includes("factorText") &&
    !research.includes("/conflict|contradict|mismatch|negative|unsupported/i"),
  "decision surface must not infer M5 conflict direction from mutable status or rationale prose",
);
assert.ok(
  research.includes("resolveEdgeProvenance(converged, edge)") &&
    research.includes("provenance?.observation_summary ?? edge.reason") &&
    research.includes("left.depth - right.depth || left.key.localeCompare(right.key)") &&
    research.includes('node.depth === 0 ? "seed" : `depth ${node.depth}`') &&
    research.includes("sequence must not be read as wall-clock time"),
  "Graph must expose canonical evidence paths and a deterministic retained sequence without fabricating observation timestamps",
);
assert.ok(
  adminPage.includes('className={caseWorkspaceActive ? "workspace caseActive" : "workspace"}') &&
    adminPage.includes('className="panel intakeDrawer"') &&
    adminPage.includes("onActiveCaseChange={handleActiveCaseChange}") &&
    adminPage.includes("(!caseWorkspaceActive || result)"),
  "active-case selection must collapse intake and promote the investigation workspace",
);
assert.ok(
  adminPage.includes('className="hero operatorAppBar"') &&
    adminPage.includes("Operator workspace") &&
    !adminPage.includes("Build the case from evidence, not assumptions."),
  "authenticated workspace must use a compact application bar rather than marketing-style hero copy",
);
assert.ok(
  adminPage.includes('type="button"') &&
    adminPage.includes('aria-keyshortcuts="n"') &&
    adminPage.includes(">New case</button>") &&
    adminPage.includes("onClick={() => setIntakeExpanded(true)}"),
  "authenticated application bar must expose a non-submitting, keyboard-discoverable new-case action wired to the existing intake drawer",
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
