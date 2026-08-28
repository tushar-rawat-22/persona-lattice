import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const source = await readFile(new URL("../app/admin/quick-research.tsx", import.meta.url), "utf8");

assert.match(source, /const \[sessionExpired, setSessionExpired\] = useState\(false\);/, "Quick Research must retain an explicit expired-session state");
assert.match(source, /response\.status === 401/, "Quick Research must classify HTTP 401 explicitly");
assert.doesNotMatch(source, /response\.status === 403[^\n]*setSessionExpired\(true\)/, "403 must remain an authorization\/policy failure, not session expiry");

for (const path of [
  "/v1/cases?limit=8",
  "/v1/cases/run-converged",
  "/v1/cases/${caseId}",
  "/v1/cases?limit=8&cursor=${encodeURIComponent(cursor)}",
]) {
  assert.ok(source.includes(path), `expected Quick Research request path ${path}`);
}

assert.match(
  source,
  /Your operator session expired[\s\S]{0,500}Sign in again/,
  "expired-session UI must explain that fresh authentication is required",
);
assert.match(source, /role="alert"/, "expired-session state must be announced accessibly");
assert.match(source, /disabled=\{[^}]*sessionExpired[^}]*\}/, "research mutations must stop once session expiry is observed");

const bodyParseBefore401 = /const body = await response\.json\(\)[\s\S]{0,220}response\.status === 401/;
assert.doesNotMatch(source, bodyParseBefore401, "mutation responses must classify 401 before consuming response bodies");

console.log("quick-research session-state contract: ok");
