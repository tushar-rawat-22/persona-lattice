import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const appRoot = path.resolve(here, "..");
const source = await readFile(path.join(appRoot, "app", "admin", "operator-system-state.tsx"), "utf8");

for (const token of [
  'type StateTone = "complete" | "partial" | "limited" | "quiet"',
  "notAttemptedLimitCount: number",
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
]) {
  assert.ok(source.includes(token), `operator system-state contract missing: ${token}`);
}

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
