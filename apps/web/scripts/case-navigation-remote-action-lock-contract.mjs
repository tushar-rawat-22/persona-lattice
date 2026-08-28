import { readFileSync } from "node:fs";

const navigation = readFileSync(new URL("../app/admin/case-navigation.tsx", import.meta.url), "utf8");
const research = readFileSync(new URL("../app/admin/quick-research.tsx", import.meta.url), "utf8");

function requireText(source, text, message) {
  if (!source.includes(text)) throw new Error(message);
}

requireText(navigation, "remoteActionsDisabled?: boolean;", "Case navigation must expose an explicit remote-action lock input.");
requireText(navigation, "remoteActionsDisabled = false,", "Remote case actions must remain enabled by default for authenticated sessions.");
requireText(navigation, "if (initialLoading || remoteActionsDisabled) return;", "Destructive confirmation handlers must fail closed during initial loading and when remote actions are locked.");
requireText(navigation, "disabled={initialLoading || remoteActionsDisabled}", "Refresh must remain disabled during initial loading and after session expiry.");
requireText(navigation, "disabled={loadingMore || remoteActionsDisabled}", "Pagination must stop remote loading after session expiry.");
requireText(navigation, "role=\"status\"", "The navigation lock must explain the unavailable remote actions accessibly.");
requireText(navigation, "Search, filter, and sort the cases already loaded in this browser remain available.", "Local case navigation must remain usable while remote actions are locked.");
requireText(navigation, "remoteActionsDisabled && cases.length === 0", "An unauthenticated empty browser snapshot must not be presented as a confirmed empty retained-case index.");
requireText(navigation, "Stored case history is unavailable until you sign in again. Do not treat this workspace as empty.", "Session expiry with no loaded summaries must state that the retained-case index is unknown rather than empty.");
requireText(research, "remoteActionsDisabled={sessionExpired}", "Quick Research must bind the retained session-expiry state to CaseNavigation.");

console.log("case navigation remote-action lock contract: ok");
