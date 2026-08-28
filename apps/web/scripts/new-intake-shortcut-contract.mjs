import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const appRoot = path.resolve(here, "..");
const source = await readFile(path.join(appRoot, "app", "admin", "page.tsx"), "utf8");

for (const token of [
  'event.key.toLowerCase() !== "n"',
  'event.metaKey || event.ctrlKey || event.altKey',
  'isEditableShortcutTarget(event.target)',
  'event.preventDefault()',
  'setIntakeExpanded(true)',
  'window.addEventListener("keydown", openNewIntake)',
  'window.removeEventListener("keydown", openNewIntake)',
  'aria-keyshortcuts="n"',
  'Press N to open new intake.',
]) {
  assert.ok(source.includes(token), `new-intake shortcut contract missing: ${token}`);
}

assert.ok(
  source.includes('target.isContentEditable') &&
    source.includes('["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName)'),
  "new-intake shortcut must not steal keystrokes from editable controls",
);
assert.ok(
  source.includes('if (intakeExpanded) return;'),
  "new-intake shortcut must remain inert when intake is already open",
);

console.log("new intake shortcut contract passed");
