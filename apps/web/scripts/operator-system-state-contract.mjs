import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const appRoot = path.resolve(here, "..");
const source = await readFile(path.join(appRoot, "app", "admin", "operator-system-state.tsx"), "utf8");

for (const token of [
  'type StateTone = "complete" | "partial" | "limited" | "quiet"',
  'title: "Research completed with limits"',
  'title: "No retained match from attempted sources"',
  'title: "Some evidence was withheld by source policy"',
  'title: "Attempted sources completed"',
  'title: "Source coverage is limited"',
  "source silence, not evidence",
  "does not imply exhaustive coverage",
  "Review Sources",
  'aria-label="Research execution state"',
]) {
  assert.ok(source.includes(token), `operator system-state contract missing: ${token}`);
}

for (const forbidden of [
  "all clear",
  "no evidence exists",
  "fully verified",
  "100% complete",
]) {
  assert.ok(!source.toLowerCase().includes(forbidden), `operator state must not overclaim: ${forbidden}`);
}

console.log("Operator system-state contract passed");
