import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const appRoot = path.resolve(here, "..");
const source = await readFile(path.join(appRoot, "app", "admin", "case-navigation.tsx"), "utf8");

for (const token of [
  "const activeCaseIsHidden = Boolean(",
  "[...cases, ...remoteCases].some((item) => item.id === activeCaseId)",
  "!visibleCases.some((item) => item.id === activeCaseId)",
  "The active case is hidden by the current retained-case search or kind filter.",
  "Show active case",
  'role="status"',
  'aria-live="polite"',
  "function clearCaseFilters()",
  'setQuery("")',
  'setKindFilter("all")',
]) {
  assert.ok(source.includes(token), `active-case filter recovery contract missing: ${token}`);
}

const clearFunction = source.slice(
  source.indexOf("function clearCaseFilters()"),
  source.indexOf("function confirmDeleteCase"),
);
assert.ok(
  !clearFunction.includes("setSortOrder"),
  "show-active-case recovery must preserve the operator's chosen sort order",
);
assert.ok(
  source.includes("!activeCaseIsHidden && (") && source.includes(">Clear filters</button>"),
  "generic empty-filter recovery must not duplicate the active-case recovery action",
);

console.log("case navigation active-filter contract passed");
