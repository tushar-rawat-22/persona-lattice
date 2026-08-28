import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const appRoot = path.resolve(here, "..");
const source = await readFile(path.join(appRoot, "app", "admin", "provenance-disclosure.tsx"), "utf8");
const research = await readFile(path.join(appRoot, "app", "admin", "quick-research.tsx"), "utf8");

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

assert.ok(
  research.includes('import { ProvenanceDisclosure } from "./provenance-disclosure";'),
  "the operator workspace must bind the reviewed provenance primitive instead of leaving it as dead UI code",
);
assert.ok(
  research.includes("provenance?:") && research.includes("sourceLocator"),
  "operator-facing decision items must carry only retained source/locator provenance needed by the disclosure",
);
assert.ok(
  research.includes("<ProvenanceDisclosure") && research.includes("records={item.provenance}"),
  "corroborated evidence must expose retained provenance in one action from the decision surface",
);
assert.ok(
  research.includes("observation.source_locator") && research.includes("observation.source"),
  "decision provenance must resolve from retained observations rather than manufactured run identifiers",
);

console.log("provenance disclosure contract passed");
