import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const appRoot = path.resolve(here, "..");
const home = await readFile(path.join(appRoot, "app", "page.tsx"), "utf8");
const desk = await readFile(path.join(appRoot, "app", "investigation-desk.tsx"), "utf8");
const sourceRuns = await readFile(path.join(appRoot, "app", "public-source-runs.ts"), "utf8");
const styles = await readFile(path.join(appRoot, "app", "public.module.css"), "utf8");

for (const token of [
  'import { InvestigationDesk } from "./investigation-desk"',
  "<InvestigationDesk />",
  "Public synthetic investigation · read only",
  "Trace a clue to evidence, provenance, and the questions left open.",
  "Open the full synthetic investigation",
  'href="/operator-access"',
]) {
  assert.ok(home.includes(token), `public first impression is missing required investigation-desk framing: ${token}`);
}

for (const token of [
  '"use client"',
  'import { syntheticCase } from "./dashboard/fixture"',
  'import { simulatedSourceRuns } from "./public-source-runs"',
  "Case & clues",
  "Source coverage",
  "Evidence path",
  "Provenance inspector",
  "Contradiction retained",
  "Unknown / coverage limit",
  "Human decision required",
  'aria-pressed={selectedId === item.observation.id}',
  "setSelectedId(item.observation.id)",
  "observation.provenance.source_name",
  "observation.provenance.source_locator",
  "observation.retrieved_at",
  "observation.freshness",
  "factor.veto || factor.applied_weight < 0",
  'link.relation === "supports"',
  'factor.status !== "applied" || factor.applied_weight === 0',
]) {
  assert.ok(desk.includes(token), `investigation desk lost a required comprehension or evidence-truth affordance: ${token}`);
}

for (const token of [
  'state: "executed"',
  'reason: "results_returned"',
  'state: "not_found"',
  'reason: "no_match"',
  'state: "unavailable"',
  'reason: "optional_not_configured"',
  'state: "review_required"',
  'reason: "review_gate"',
  'reason: "remote_rate_limit"',
]) {
  assert.ok(sourceRuns.includes(token), `shared public source-state fixture is missing: ${token}`);
}

assert.ok(
  desk.includes("sourceRun.attempted") &&
    desk.includes('sourceRun.state === "not_found"') &&
    desk.includes('sourceRun.state === "review_required"'),
  "source coverage must distinguish attempted no-match, review-gated and unavailable states",
);

for (const token of [
  ".deskShell",
  "font-size: clamp(30px, 3.7vw, 52px)",
  "grid-template-columns: minmax(210px, 0.68fr) minmax(0, 1.35fr) minmax(240px, 0.82fr)",
  ".deskEvidenceButton:focus-visible",
  "min-height: 44px",
  "@media (max-width: 980px)",
  "@media (max-width: 680px)",
  "@media (prefers-reduced-motion: reduce)",
]) {
  assert.ok(styles.includes(token), `investigation desk CSS is missing exact responsive/accessibility coverage: ${token}`);
}

for (const forbidden of [
  "evidence casebook",
  "font-family: Georgia",
  "radial-gradient(",
  "linear-gradient(",
  "three",
  "webgl",
  "canvas",
]) {
  assert.ok(!home.toLowerCase().includes(forbidden), `public home retained forbidden editorial/decorative framing: ${forbidden}`);
}

for (const forbidden of ["fetch(", "localStorage", "sessionStorage", "/v1/", "identity probability"] ) {
  assert.ok(!desk.includes(forbidden), `public desk must remain fixture-backed and non-operational: ${forbidden}`);
}

console.log("Investigation desk first-impression contract passed");
