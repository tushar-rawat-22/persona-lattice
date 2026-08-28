import fs from "node:fs";
import path from "node:path";

const root = process.cwd();
const source = fs.readFileSync(path.join(root, "app/admin/upload-review-workflow.tsx"), "utf8");

const required = [
  'const [sessionExpired, setSessionExpired] = useState(false);',
  'if (response.status !== 401) return;',
  'setSessionExpired(true);',
  'role="alert"',
  'Review state has not been changed by the rejected request.',
  'const actionsDisabled = busy || sessionExpired;',
  'disabled={actionsDisabled}',
  'disabled={actionsDisabled || !csrfToken}',
];

for (const fragment of required) {
  if (!source.includes(fragment)) {
    throw new Error(`upload review session-state contract missing: ${fragment}`);
  }
}

const guardCalls = source.match(/requireActiveSession\(response\);/g) ?? [];
if (guardCalls.length !== 3) {
  throw new Error(`expected session guard on all 3 upload-review mutations, found ${guardCalls.length}`);
}

for (const mutation of ["mutateReview", "promote", "runCase"]) {
  const start = source.indexOf(`async function ${mutation}`);
  if (start < 0) throw new Error(`missing ${mutation}`);
  const next = source.indexOf("\n  async function ", start + 1);
  const block = source.slice(start, next < 0 ? source.length : next);
  const guard = block.indexOf("requireActiveSession(response);");
  const bodyRead = block.indexOf("await response.json()");
  if (guard < 0 || bodyRead < 0 || guard > bodyRead) {
    throw new Error(`${mutation} must classify 401 before consuming the response body`);
  }
}

if (/response\.status\s*===\s*403[\s\S]{0,120}setSessionExpired/.test(source)) {
  throw new Error("403 must not be mislabeled as an expired authentication session");
}

console.log("upload review session-state contract: PASS");
