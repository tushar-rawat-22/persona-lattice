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
  "factor.veto",
  "factor.applied_weight < 0",
  "factor.applied_weight > 0",
  '/conflict|contradict|mismatch|negative|unsupported/i',
  "Math.abs(right.applied_weight) - Math.abs(left.applied_weight)",
  'label="Supporting"',
  'label="Conflicting"',
  'label="Neutral / withheld"',
  "rows.slice(0, 3)",
  "not calibrated probabilities",
  "do not establish identity",
]) {
  assert.ok(source.includes(token), `M5 decisive-factor contract missing: ${token}`);
}

assert.ok(
  !/identity[_ ]probability\s*[:=]\s*[^n]/i.test(source),
  "M5 summary must not introduce a numeric identity-probability channel",
);
assert.ok(
  source.includes("vetoDelta") && source.includes("localeCompare"),
  "decisive-factor ordering must remain deterministic when absolute weights tie",
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
