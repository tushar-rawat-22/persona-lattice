import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const appRoot = path.resolve(here, "..");
const source = await readFile(path.join(appRoot, "app", "admin", "case-navigation.tsx"), "utf8");

for (const token of [
  'useRef<HTMLInputElement>(null)',
  'event.key !== "/"',
  'event.metaKey || event.ctrlKey || event.altKey',
  'isEditableShortcutTarget(event.target)',
  'event.preventDefault()',
  'searchInputRef.current.focus()',
  'window.addEventListener("keydown", focusCaseSearch)',
  'window.removeEventListener("keydown", focusCaseSearch)',
  'aria-keyshortcuts="/"',
  'Press / to focus. Search is limited to case ID, identifier kind, and identifier value.',
]) {
  assert.ok(source.includes(token), `case-search shortcut contract missing: ${token}`);
}

assert.ok(
  source.includes('target.isContentEditable') &&
    source.includes('["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName)'),
  "case-search shortcut must not steal slash keystrokes from editable controls",
);
assert.ok(
  source.includes('if (!searchInputRef.current) return;'),
  "case-search shortcut must remain inert when the retained-case search is not rendered",
);

console.log("case navigation shortcut contract passed");
