import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const navigation = readFileSync(new URL("../app/admin/case-navigation.tsx", import.meta.url), "utf8");

assert.match(
  navigation,
  /export function caseRetentionStatus\(expiresAt: string, nowMs = Date\.now\(\)\)/,
  "case navigation must expose a deterministic retention-deadline classifier",
);
assert.match(navigation, /Date\.parse\(expiresAt\)/, "retention state must derive from the retained expires_at deadline");
assert.match(
  navigation,
  /!Number\.isFinite\(expiresMs\).*"unknown"/,
  "malformed historical retention deadlines must fail closed as unknown",
);
assert.match(
  navigation,
  /expiresMs <= nowMs \? "elapsed" : "active"/,
  "elapsed retention must be classified from the explicit deadline rather than an arbitrary age threshold",
);
assert.match(navigation, /Retention deadline passed/, "elapsed rows must be explicit to the operator");
assert.match(navigation, /refresh before relying on this row/, "stale rows must direct the operator to refresh before relying on them");
assert.match(navigation, /Retention deadline unavailable/, "unknown historical deadlines must not be rendered as active retention");
assert.match(navigation, /Retained until/, "active rows must continue to expose their exact retention deadline");
assert.match(navigation, /onClick=\{\(\) => onOpenCase\(item\.id\)\}/, "retention state must not invent client-side authorization or deletion semantics");
assert.doesNotMatch(
  navigation,
  /disabled=\{[^}]*retentionStatus/,
  "the client must not infer that an elapsed local deadline makes the server-side case inaccessible",
);

console.log("case retention state contract: PASS");
