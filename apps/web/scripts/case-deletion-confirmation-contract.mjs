import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const appRoot = path.join(here, "..");
const source = await readFile(path.join(appRoot, "app", "admin", "case-navigation.tsx"), "utf8");
const quickResearch = await readFile(path.join(appRoot, "app", "admin", "quick-research.tsx"), "utf8");

for (const token of [
  'const [pendingDeleteCaseId, setPendingDeleteCaseId] = useState<string | null>(null)',
  'pendingDeleteCaseId === item.id',
  'Delete this retained case? This cannot be undone.',
  'Confirm delete',
  'aria-live="polite"',
  'onClick={() => setPendingDeleteCaseId(item.id)}',
  'onClick={() => confirmDeleteCase(item.id)}',
  'onClick={() => setPendingDeleteCaseId(null)}',
  'const [pendingDeleteAll, setPendingDeleteAll] = useState(false)',
  'Delete every retained private research case? This cannot be undone.',
  'Confirm delete all',
  'onClick={() => setPendingDeleteAll(true)}',
  'onClick={confirmDeleteAll}',
  'onClick={() => setPendingDeleteAll(false)}',
]) {
  assert.ok(source.includes(token), `case deletion confirmation contract missing: ${token}`);
}

const singleConfirmationHandler = source.match(
  /function confirmDeleteCase\(caseId: string\) \{([\s\S]*?)\n  \}/,
)?.[1] ?? "";
assert.ok(
  singleConfirmationHandler.includes("onDeleteCase(caseId);") &&
    singleConfirmationHandler.includes("setPendingDeleteCaseId(null);"),
  "confirmed single-case deletion must invoke the destructive callback and then leave confirmation state",
);

const bulkConfirmationHandler = source.match(
  /function confirmDeleteAll\(\) \{([\s\S]*?)\n  \}/,
)?.[1] ?? "";
assert.ok(
  bulkConfirmationHandler.includes("onDeleteAll();") &&
    bulkConfirmationHandler.includes("setPendingDeleteAll(false);"),
  "confirmed bulk deletion must invoke the destructive callback and then leave confirmation state",
);

assert.ok(
  !source.includes('onClick={() => onDeleteCase(item.id)}'),
  "single-case deletion must not invoke the destructive callback directly from the first action",
);
assert.ok(
  !source.includes('onClick={onDeleteAll}'),
  "bulk deletion must not invoke the destructive callback directly from the first action",
);
assert.ok(
  !quickResearch.includes('window.confirm("Delete every retained private research case?")'),
  "bulk deletion confirmation must live in the retained-case surface instead of a browser modal",
);

console.log("Case deletion confirmation contract passed");
