import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const source = await readFile(path.join(here, "..", "app", "admin", "case-navigation.tsx"), "utf8");

for (const token of [
  'const [pendingDeleteCaseId, setPendingDeleteCaseId] = useState<string | null>(null)',
  'pendingDeleteCaseId === item.id',
  'Delete this retained case? This cannot be undone.',
  'Confirm delete',
  'Cancel',
  'aria-live="polite"',
  'onClick={() => setPendingDeleteCaseId(item.id)}',
  'onClick={() => confirmDeleteCase(item.id)}',
  'onClick={() => setPendingDeleteCaseId(null)}',
]) {
  assert.ok(source.includes(token), `case deletion confirmation contract missing: ${token}`);
}

const confirmationHandler = source.match(
  /function confirmDeleteCase\(caseId: string\) \{([\s\S]*?)\n  \}/,
)?.[1] ?? "";
assert.ok(
  confirmationHandler.includes("onDeleteCase(caseId);") &&
    confirmationHandler.includes("setPendingDeleteCaseId(null);"),
  "confirmed deletion must invoke the destructive callback and then leave confirmation state",
);

assert.ok(
  !source.includes('onClick={() => onDeleteCase(item.id)}'),
  "single-case deletion must not invoke the destructive callback directly from the first action",
);

console.log("Case deletion confirmation contract passed");
