import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const appRoot = path.resolve(here, "..");
const source = await readFile(path.join(appRoot, "app", "admin", "case-navigation.tsx"), "utf8");

assert.ok(
  source.includes("No retained cases match the current search and kind filter."),
  "filtered-empty state must remain explicit rather than pretending retained history is empty",
);
assert.ok(
  source.includes(">Clear filters</button>") &&
    source.includes('setQuery("")') &&
    source.includes('setKindFilter("all")'),
  "filtered-empty state must let the operator recover without manually clearing multiple controls",
);
assert.ok(
  !source.includes('setSortOrder("newest")'),
  "clearing search and kind filters must preserve the operator's chosen sort order",
);

console.log("case navigation clear-filter contract: PASS");
