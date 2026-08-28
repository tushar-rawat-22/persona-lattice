import { readFileSync } from "node:fs";

const navigation = readFileSync(new URL("../app/admin/case-navigation.tsx", import.meta.url), "utf8");
const research = readFileSync(new URL("../app/admin/quick-research.tsx", import.meta.url), "utf8");

function requireText(source, text, message) {
  if (!source.includes(text)) throw new Error(message);
}

requireText(navigation, "initialLoading?: boolean;", "Case navigation must distinguish first-load state from a confirmed empty case list.");
requireText(navigation, "initialLoading = false,", "Case navigation loading state must remain opt-in for existing callers.");
requireText(navigation, "Loading retained cases…", "Initial case loading must be explicit to the operator.");
requireText(navigation, "No retained research cases yet.", "Confirmed empty case state must remain distinct from loading.");
requireText(navigation, "aria-busy={initialLoading}", "Stored case navigation must expose first-load busy state accessibly.");
requireText(navigation, "disabled={initialLoading || remoteActionsDisabled}", "Refresh must not start a competing first-load request.");
requireText(navigation, "if (initialLoading || remoteActionsDisabled) return;", "Destructive handlers must fail closed while the initial case list is unresolved.");
requireText(research, "const [initialCasesLoading, setInitialCasesLoading] = useState(true);", "Quick Research must retain an explicit initial case-loading state.");
requireText(research, "initialLoading={initialCasesLoading}", "Quick Research must bind first-load state to CaseNavigation.");
requireText(research, "setInitialCasesLoading(false);", "Initial case loading must reach a terminal state after the first retained-case request settles.");

console.log("case navigation loading-state contract: ok");
