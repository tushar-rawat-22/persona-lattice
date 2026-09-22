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

const cspLine = headers
  .split(/\r?\n/)
  .map((line) => line.trim())
  .find((line) => line.startsWith("Content-Security-Policy:"));
if (!cspLine) throw new Error("public demo export missing CSP policy");

const csp = cspLine.slice("Content-Security-Policy:".length).trim();
const requiredCspDirectives = [
  "default-src 'self'",
  "base-uri 'self'",
  "form-action 'self'",
  "frame-ancestors 'none'",
  "object-src 'none'",
  "script-src 'self' 'unsafe-inline'",
  "style-src 'self' 'unsafe-inline'",
  "connect-src 'none'",
  "img-src 'self' data:",
  "font-src 'self'",
  "manifest-src 'self'",
  "worker-src 'self'",
];
for (const directive of requiredCspDirectives) {
  if (!csp.split(";").map((part) => part.trim()).includes(directive)) {
    throw new Error(`public demo CSP missing or broadened directive: ${directive}`);
  }
}
for (const forbidden of ["*", "https:", "http:", "data:*"]) {
  if (csp.split(/\s+/).includes(forbidden)) {
    throw new Error(`public demo CSP contains forbidden broad source: ${forbidden}`);
  }
}

const operatorBoundary = fs.readFileSync(path.join(out, "operator-access", "index.html"), "utf8");
if (!operatorBoundary.includes("The public demo does not expose research authority.")) {
  throw new Error("public demo operator boundary page lost its non-operational framing");
}

const forbiddenRuntimeMarkers = ["Unlock operator console", "/v1/auth/login"];
const textAssetExtensions = new Set([".css", ".html", ".js", ".json", ".map", ".txt"]);

function walkTextAssets(directory) {
  const assets = [];
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    const absolute = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      assets.push(...walkTextAssets(absolute));
      continue;
    }
    if (entry.isFile() && textAssetExtensions.has(path.extname(entry.name))) {
      assets.push(absolute);
    }
  }
  return assets;
}

for (const absolute of walkTextAssets(out)) {
  const relative = path.relative(out, absolute);
  const body = fs.readFileSync(absolute, "utf8");
  for (const marker of forbiddenRuntimeMarkers) {
    if (body.includes(marker)) {
      throw new Error(
        `public artifact ${relative} contains private runtime marker ${JSON.stringify(marker)}`,
      );
    }
  }
}

console.log("public demo static export contract passed");
