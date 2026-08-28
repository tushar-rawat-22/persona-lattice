import { readFileSync } from "node:fs";

const page = readFileSync(new URL("../app/admin/page.tsx", import.meta.url), "utf8");

function requireText(text, message) {
  if (!page.includes(text)) throw new Error(message);
}

requireText("<summary>Inspect intake mechanics</summary>", "Authenticated intake provider/runtime mechanics must live behind an explicit disclosure.");
requireText("<pre>{JSON.stringify(result.normalized, null, 2)}</pre>", "The retained normalized payload must remain available for operator inspection.");
requireText("result.provider_plan.map", "The retained provider policy plan must remain available for operator inspection.");

const disclosureIndex = page.indexOf("<summary>Inspect intake mechanics</summary>");
const normalizedIndex = page.indexOf("<pre>{JSON.stringify(result.normalized, null, 2)}</pre>");
const providerPlanIndex = page.indexOf("result.provider_plan.map");
if (disclosureIndex < 0 || normalizedIndex < disclosureIndex || providerPlanIndex < disclosureIndex) {
  throw new Error("Raw normalization and provider planning must be nested after the intake-mechanics disclosure rather than appearing in the default scan path.");
}

requireText("Provider/runtime details are implementation mechanics, not findings.", "The disclosure must explain why provider/runtime internals are secondary to findings.");

console.log("intake mechanics disclosure contract: ok");
