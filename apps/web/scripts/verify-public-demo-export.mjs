import fs from "node:fs";
import path from "node:path";

const root = process.cwd();
const out = path.join(root, "out");
const requiredFiles = [
  "index.html",
  path.join("demo", "index.html"),
  path.join("operator-access", "index.html"),
  "404.html",
  "_headers",
  "_redirects",
];

for (const relative of requiredFiles) {
  const target = path.join(out, relative);
  if (!fs.existsSync(target)) throw new Error(`public demo export missing ${relative}`);
}

for (const relative of [
  "admin",
  path.join("_next", "static", "chunks", "app", "admin"),
]) {
  if (fs.existsSync(path.join(out, relative))) {
    throw new Error(`public demo export leaked private operator artifact: ${relative}`);
  }
}

const redirects = fs.readFileSync(path.join(out, "_redirects"), "utf8");
for (const rule of ["/admin /operator-access/ 302", "/admin/* /operator-access/ 302"]) {
  if (!redirects.includes(rule)) throw new Error(`public demo export missing admin isolation rule: ${rule}`);
}

const headers = fs.readFileSync(path.join(out, "_headers"), "utf8");
for (const header of [
  "Content-Security-Policy:",
  "X-Content-Type-Options: nosniff",
  "X-Frame-Options: DENY",
  "Referrer-Policy: no-referrer",
  "Permissions-Policy:",
  "Strict-Transport-Security:",
]) {
  if (!headers.includes(header)) throw new Error(`public demo export missing security header: ${header}`);
}

const operatorBoundary = fs.readFileSync(path.join(out, "operator-access", "index.html"), "utf8");
if (!operatorBoundary.includes("The public demo does not expose research authority.")) {
  throw new Error("public demo operator boundary page lost its non-operational framing");
}

const forbiddenRuntimeMarkers = [
  "Unlock operator console",
  "/v1/auth/login",
  "NEXT_PUBLIC_API_URL",
];
function inspectTree(directory) {
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    const target = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      inspectTree(target);
      continue;
    }
    if (!/\.(?:html|js|json|txt)$/i.test(entry.name)) continue;
    const body = fs.readFileSync(target, "utf8");
    for (const marker of forbiddenRuntimeMarkers) {
      if (body.includes(marker)) {
        throw new Error(
          `public demo export contains private runtime marker ${JSON.stringify(marker)} in ${path.relative(out, target)}`,
        );
      }
    }
  }
}
inspectTree(out);

console.log("public demo static export contract passed");
