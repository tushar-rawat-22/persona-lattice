import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const appRoot = path.resolve(here, "..");
const source = await readFile(path.join(appRoot, "app", "admin", "m5-factor-summary.tsx"), "utf8");
const quickResearch = await readFile(path.join(appRoot, "app", "admin", "quick-research.tsx"), "utf8");

for (const token of [
  'type FactorClass = "supporting" | "conflicting" | "neutral"',
  "factor.veto || factor.applied_weight < 0",
  "factor.applied_weight > 0",
  "Math.abs(right.applied_weight) - Math.abs(left.applied_weight)",
  'label="Supporting"',
  'label="Conflicting"',
  'label="Neutral / withheld"',
  "const visibleRows = rows.slice(0, 3)",
  "const hiddenCount = Math.max(0, rows.length - visibleRows.length)",
  "more retained",
  "in the full ledger below",
  "not calibrated probabilities",
  "do not establish identity",
]) {
  assert.ok(source.includes(token), `M5 decisive-factor contract missing: ${token}`);
}

assert.ok(
  !source.includes("factor.status} ${factor.rationale") &&
    !source.includes("/conflict|contradict|mismatch|negative|unsupported/i"),
  "M5 evidentiary direction must never be inferred from mutable status/rationale prose",
);
assert.ok(
  source.includes('hiddenCount === 1 ? "factor" : "factors"'),
  "truncated M5 summaries must disclose the exact hidden-factor count without awkward singular copy",
);
assert.ok(
  !/identity[_ ]probability\s*[:=]\s*[^n]/i.test(source),
  "M5 summary must not introduce a numeric identity-probability channel",
);
const vetoOrder = source.indexOf("const vetoDelta = Number(right.veto) - Number(left.veto)");
const weightOrder = source.indexOf("const weightDelta = Math.abs(right.applied_weight) - Math.abs(left.applied_weight)");
assert.ok(
  vetoOrder >= 0 && weightOrder >= 0 && vetoOrder < weightOrder && source.includes("localeCompare"),
  "decisive-factor ordering must keep retained vetoes visible before magnitude ranking and remain deterministic on ties",
);

for (const token of [
  'import { M5FactorSummary } from "./m5-factor-summary";',
  "<M5FactorSummary factors={evaluation.factors} />",
  '<details className="evidenceFactors">',
]) {
  assert.ok(
    quickResearch.includes(token),
    `M5 candidate-card integration contract missing: ${token}`,
  );
}
assert.ok(
  quickResearch.indexOf("<M5FactorSummary factors={evaluation.factors} />") <
    quickResearch.indexOf('<details className="evidenceFactors">'),
  "decisive-factor summary must appear before the full retained factor ledger",
);

console.log("M5 factor summary contract passed");
