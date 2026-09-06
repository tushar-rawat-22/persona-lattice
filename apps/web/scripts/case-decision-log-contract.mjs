import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const sourcePath = path.resolve(process.cwd(), "app/admin/case-brief.tsx");
const source = fs.readFileSync(sourcePath, "utf8");

const required = [
  'type CaseDecisionDisposition =',
  '"continue_research"',
  '"await_more_evidence"',
  '"ready_for_handoff"',
  '"close_case"',
  '/decisions`, {',
  'method: "POST"',
  '"X-PersonaLattice-CSRF"',
  'maxLength={1200}',
  'aria-label="Analyst decision log"',
  'Append-only rationale retained with this case',
  'Do not treat this case as having no prior analyst decisions.',
  'Decisions are analyst-authored workflow records, not evidence and not identity claims.',
];

for (const marker of required) {
  if (!source.includes(marker)) {
    throw new Error(`case decision log contract missing: ${marker}`);
  }
}

if (!source.includes('items: [created, ...(current?.caseId === caseId ? current.items : [])]')) {
  throw new Error("new decisions must appear immediately without replacing retained history");
}

if (!source.includes('if (created.case_id !== caseId)')) {
  throw new Error("decision responses must remain bound to the active retained case");
}

if (source.includes("identity_confirmed") || source.includes("identity_verified")) {
  throw new Error("analyst workflow decisions must not create identity-claim states");
}

console.log("case decision log contract: PASS");
