import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const appRoot = path.resolve(here, "..");
const styles = await readFile(path.join(appRoot, "app", "globals.css"), "utf8");
const globalStyles = styles.slice(0, styles.indexOf("@media (min-width: 1180px)"));

assert.match(
  styles,
  /@media \(max-width: 980px\)[\s\S]*?\.researchWorkbench\.activeResearch \.recentCases > \.providerList \{\s*display:\s*flex;/,
  "narrow retained-case scrolling must apply only to the direct case list, not nested decision-state lists",
);

assert.ok(
  !styles.includes(".researchWorkbench.activeResearch .recentCases .providerList { display: flex;"),
  "narrow retained-case scrolling must not flatten nested decision-state lists into horizontal columns",
);

for (const [pattern, message] of [
  [
    /\.caseNavigationEmptyState\[aria-label="Retained case decision brief"\] \.provider \{\s*align-items:\s*flex-start;\s*flex-direction:\s*column;/,
    "decision states must stack in the 220px desktop rail as well as at exact 390/320",
  ],
  [
    /\.researchWorkbench\.activeResearch \.recentCases \.panelHeader > div \{\s*align-items:\s*start;\s*display:\s*grid;/,
    "the stored-case rail heading must not squeeze its title and description into competing columns",
  ],
  [
    /\.workspace\.caseActive \.intakeSummary \{\s*align-items:\s*flex-start;\s*flex-direction:\s*column;/,
    "the collapsed intake rail must stack its action below its summary when a case is active",
  ],
  [
    /\.workspace\.caseActive \.summaryAction \{\s*display:\s*flex;\s*flex-wrap:\s*wrap;\s*gap:\s*4px;\s*white-space:\s*normal;/,
    "the active-case intake action and keyboard hint must remain distinct instead of running together",
  ],
]) {
  assert.match(globalStyles, pattern, message);
}

console.log("Narrow workspace reflow contract passed");
