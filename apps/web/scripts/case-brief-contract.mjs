import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const root = process.cwd();
const briefPath = path.join(root, "app", "admin", "case-brief.tsx");
const navigationPath = path.join(root, "app", "admin", "case-navigation.tsx");
const brief = fs.readFileSync(briefPath, "utf8");
const navigation = fs.readFileSync(navigationPath, "utf8");

const requiredBriefFragments = [
  "/v1/cases/${encodeURIComponent(caseId)}",
  'credentials: "include"',
  "case brief identity mismatch",
  "observationCount",
  "sourceCount",
  "contradictionCount",
  "warningCount",
  "coverageGapCount: number | null",
  "coverageGapCount: null",
  "executiveSummary.truncated === true",
  "coverage gaps not recorded",
  "Decision brief",
  "Corroborated",
  "Not classified by retained report",
  "Do not infer corroboration from observation count.",
  "Conflicting",
  "No recorded conflicts is not proof that the evidence is consistent.",
  "Unknown",
  "unknown must not be presented as none.",
  "Traversal limit reached. Treat unexplored leads as open questions rather than negative findings.",
  "Coverage gaps are retained report findings, not evidence of absence.",
  "Source states:",
  "No identity probability is calculated",
  "same-handle overlap is not identity proof",
  "Inspect canonical observations for evidence and provenance",
];

for (const fragment of requiredBriefFragments) {
  if (!brief.includes(fragment)) throw new Error(`case brief contract missing: ${fragment}`);
}

if (brief.includes("coverageGapCount: 0")) {
  throw new Error("converged case brief must not invent zero coverage gaps when none are recorded");
}

for (const forbiddenInference of ["corroboratedObservationCount", "corroborationCount", "identityProbability"]) {
  if (brief.includes(forbiddenInference)) throw new Error(`case brief must not infer unsupported decision metric: ${forbiddenInference}`);
}

if (!navigation.includes('<CaseBrief caseId={activeCaseId} disabled={remoteActionsDisabled} />')) {
  throw new Error("case brief must be bound to the active retained case and session lock state");
}

for (const forbidden of ["source_locator", "seed_value", "provider detail", "identity_probability"]) {
  if (brief.includes(forbidden)) throw new Error(`case brief must not duplicate sensitive/detail field: ${forbidden}`);
}

console.log("case brief contract: PASS");
