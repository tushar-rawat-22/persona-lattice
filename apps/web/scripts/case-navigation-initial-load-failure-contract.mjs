import { readFileSync } from "node:fs";

const navigation = readFileSync(new URL("../app/admin/case-navigation.tsx", import.meta.url), "utf8");
const research = readFileSync(new URL("../app/admin/quick-research.tsx", import.meta.url), "utf8");

function requireText(source, text, message) {
  if (!source.includes(text)) throw new Error(message);
}

requireText(navigation, "initialLoadFailed?: boolean;", "Case navigation must distinguish a failed initial index load from a confirmed empty index.");
requireText(navigation, "initialLoadFailed = false,", "Initial load failure must remain opt-in for callers with a known successful index state.");
requireText(navigation, "Stored case history could not be loaded. Refresh before treating this workspace as empty.", "Failed initial case loading must not render as a confirmed empty workspace.");
requireText(navigation, "initialLoadFailed && cases.length === 0", "Failure copy must be reserved for an unavailable empty index rather than hiding already-loaded case summaries.");
requireText(research, "const [initialCasesLoadFailed, setInitialCasesLoadFailed] = useState(false);", "Quick Research must retain explicit initial case-index failure state.");
requireText(research, "initialLoadFailed={initialCasesLoadFailed}", "Quick Research must bind initial case-index failure to CaseNavigation.");
requireText(research, "setInitialCasesLoadFailed(true);", "The initial case request must record non-auth transport or HTTP failure.");
requireText(research, "setInitialCasesLoadFailed(false);", "A successful case-index load or refresh must clear a prior initial-load failure.");

console.log("case navigation initial-load failure contract: ok");
