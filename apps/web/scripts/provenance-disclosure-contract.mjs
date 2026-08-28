import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const appRoot = path.resolve(here, "..");
const source = await readFile(path.join(appRoot, "app", "admin", "provenance-disclosure.tsx"), "utf8");

for (const token of [
  'parsed.username || parsed.password || !parsed.hostname',
  'normalized.endsWith(".localhost")',
  'normalized.endsWith(".local")',
  'normalized.endsWith(".internal")',
  '!normalized.includes(".")',
  'hostname.includes(":")',
  'target="_blank"',
  'rel="noopener noreferrer"',
  'aria-label={`Open canonical source for ${record.source}`}',
]) {
  assert.ok(source.includes(token), `provenance navigation lost fail-closed boundary: ${token}`);
}

assert.ok(
  source.includes('/^\\d{1,3}(?:\\.\\d{1,3}){3}$/.test(hostname)'),
  "provenance navigation must refuse IPv4 literals instead of opening operator-local/private targets",
);
assert.ok(
  source.includes('["http:", "https:"].includes(parsed.protocol)'),
  "provenance navigation must remain limited to ordinary web locators",
);
assert.ok(
  source.includes("candidate.source === record.source") &&
    source.includes("candidate.sourceLocator === record.sourceLocator"),
  "provenance records may deduplicate only exact source/locator pairs",
);

console.log("provenance disclosure contract passed");
