import { readFileSync } from "node:fs";

const navigation = readFileSync(new URL("../app/admin/case-navigation.tsx", import.meta.url), "utf8");
const research = readFileSync(new URL("../app/admin/quick-research.tsx", import.meta.url), "utf8");

function requireText(source, text, message) {
  if (!source.includes(text)) throw new Error(message);
}

requireText(navigation, "remoteActionsDisabled?: boolean;", "Case navigation must expose an explicit remote-action lock input.");
requireText(navigation, "remoteActionsDisabled = false,", "Remote case actions must remain enabled by default for authenticated sessions.");
requireText(navigation, "if (remoteActionsDisabled) return;", "Destructive confirmation handlers must fail closed when remote actions are locked.");
requireText(navigation, "disabled={remoteActionsDisabled}", "Remote case controls must render disabled after session expiry.");
requireText(navigation, "disabled={loadingMore || remoteActionsDisabled}", "Pagination must stop remote loading after session expiry.");
requireText(navigation, "role=\"status\"", "The navigation lock must explain the unavailable remote actions accessibly.");
requireText(navigation, "Search, filter, and sort the cases already loaded in this browser remain available.", "Local case navigation must remain usable while remote actions are locked.");
requireText(research, "remoteActionsDisabled={sessionExpired}", "Quick Research must bind the retained session-expiry state to CaseNavigation.");

console.log("case navigation remote-action lock contract: ok");
