import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const appRoot = path.resolve(here, "..");
const source = await readFile(path.join(appRoot, "app", "admin", "case-navigation.tsx"), "utf8");

for (const token of [
  'const REMOTE_SEARCH_LIMIT = 50;',
  'const REMOTE_SEARCH_DEBOUNCE_MS = 250;',
  'function retainedCaseSearchPath(query: string, kind: KindFilter): string',
  'params.set("q", normalized)',
  'params.set("kind", kind)',
  'credentials: "include"',
  'signal: controller.signal',
  'response.headers.get("X-PersonaLattice-Next-Cursor")',
  'Full retained-case search is unavailable.',
  'do not treat an empty result as proof that no retained case exists.',
  'Search retained case metadata without loading retained report payloads.',
  'Search is limited to case ID, identifier kind, and identifier value.',
  '!remoteFiltering && hasMore',
]) {
  assert.ok(source.includes(token), `server retained-case search contract missing: ${token}`);
}

assert.ok(
  source.includes('const remoteSearchActive = remoteFiltering && !remoteActionsDisabled;') &&
    source.includes('const sourceCases = remoteSearchActive && !remoteSearchFailed ? remoteCases : cases;'),
  "remote results must replace loaded-only filtering only while an authenticated retained-index filter is active",
);
assert.ok(
  source.includes('setRemoteSearchFailed(true);') && source.includes('setRemoteCases([]);'),
  "failed remote search must fail visibly and fall back to locally loaded metadata",
);
const inactiveBranch = source.slice(
  source.indexOf('if (!remoteSearchActive) {'),
  source.indexOf('const generation = ++remoteSearchGeneration.current;'),
);
assert.ok(
  !inactiveBranch.includes('setRemote'),
  "inactive remote-search state must be derived rather than synchronously reset inside the effect",
);
assert.ok(
  !source.includes('report_json') && !source.includes('reportPayload'),
  "case navigation must remain metadata-only and never request or inspect retained report payloads",
);

console.log("case navigation server-search contract passed");
