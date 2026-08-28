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

assert.ok(
  source.indexOf('onClick={() => setPendingDeleteCaseId(item.id)}') < source.indexOf('onClick={() => confirmDeleteCase(item.id)}'),
  "single-case deletion must enter an explicit confirmation state before invoking deletion",
);

assert.ok(
  !source.includes('onClick={() => onDeleteCase(item.id)}'),
  "single-case deletion must not invoke the destructive callback directly from the first action",
);

console.log("Case deletion confirmation contract passed");
