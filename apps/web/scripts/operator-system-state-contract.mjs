import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const appRoot = path.resolve(here, "..");
const source = await readFile(path.join(appRoot, "app", "admin", "operator-system-state.tsx"), "utf8");
const model = await readFile(path.join(appRoot, "app", "admin", "operator-system-state-model.ts"), "utf8");
const quickResearch = await readFile(path.join(appRoot, "app", "admin", "quick-research.tsx"), "utf8");

for (const token of [
  'type StateTone = "complete" | "partial" | "limited" | "quiet"',
  'title: "Research completed with limits"',
  'title: "Some evidence was withheld by source policy"',
  'title: "Some source paths were not attempted"',
  'title: "No retained match from attempted sources"',
  'title: "Attempted sources completed"',
  'title: "Source coverage is limited"',
  "configuration, routing, review, budget or policy limits before provider contact",
  "source silence, not evidence",
  "does not imply exhaustive coverage",
  "Review Sources",
  'aria-label="Research execution state"',
  'import type { OperatorSystemStateCounts } from "./operator-system-state-model"',
]) {
  assert.ok(source.includes(token), `operator system-state contract missing: ${token}`);
}

for (const token of [
  "notAttemptedLimitCount: number",
  "export function operatorSystemStateCounts",
  "export function operatorSystemStateCountsFromSourceRuns",
  "item?.evaluation?.aggregate",
  "aggregate.unclassified_attempt_count",
  "aggregate.queued_count",
  "aggregate.review_required_count",
  "aggregate.routing_unavailable_count",
  "aggregate.local_budget_stop_count",
  "aggregate.optional_not_configured_count",
  "aggregate.missing_secret_config_count",
  "aggregate.provider_policy_block_count",
  "aggregate.display_only_count",
  "aggregate.blocked_count",
]) {
  assert.ok(model.includes(token), `operator system-state aggregation contract missing: ${token}`);
}

for (const token of [
  'import { OperatorSystemState } from "./operator-system-state"',
  'operatorSystemStateCountsFromSourceRuns',
  '<OperatorSystemState {...systemStateCounts} />',
  'converged.nodes.map((node) => node.source_runs)',
  'operatorSystemStateCountsFromSourceRuns([report.source_runs])',
]) {
  assert.ok(quickResearch.includes(token), `live Overview system-state binding missing: ${token}`);
}

const decisionSurfaceIndex = quickResearch.indexOf("<DecisionSurface report={report} />");
const operatorStateIndex = quickResearch.indexOf("<OperatorSystemState {...systemStateCounts} />");
const metricGridIndex = quickResearch.indexOf('<div className="reportMetricGrid">');
assert.ok(
  decisionSurfaceIndex >= 0 && operatorStateIndex > decisionSurfaceIndex && metricGridIndex > operatorStateIndex,
  "operator execution state must sit between decision synthesis and supporting metrics",
);

const withheldIndex = source.indexOf("if (withheldCount > 0)");
const notAttemptedIndex = source.indexOf("if (notAttemptedLimitCount > 0)");
const noMatchIndex = source.indexOf("if (attemptCount > 0 && noMatchCount === attemptCount)");
assert.ok(withheldIndex >= 0 && notAttemptedIndex > withheldIndex && noMatchIndex > notAttemptedIndex,
  "policy/configuration limits must take precedence over a quiet no-match state");

for (const forbidden of [
  "all clear",
  "no evidence exists",
  "fully verified",
  "100% complete",
]) {
  assert.ok(!source.toLowerCase().includes(forbidden), `operator state must not overclaim: ${forbidden}`);
}

console.log("Operator system-state contract passed");
