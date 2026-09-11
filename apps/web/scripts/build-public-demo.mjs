import { spawnSync } from "node:child_process";
import { existsSync, readFileSync, readdirSync, rmSync } from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";

const require = createRequire(import.meta.url);
const nextBin = require.resolve("next/dist/bin/next");

const inheritedKeys = [
  "CI",
  "HOME",
  "LANG",
  "LC_ALL",
  "NODE_OPTIONS",
  "PATH",
  "TEMP",
  "TMP",
  "TMPDIR",
];
const buildEnv = Object.fromEntries(
  inheritedKeys.flatMap((key) => (process.env[key] ? [[key, process.env[key]]] : [])),
);
buildEnv.NODE_ENV = "production";
buildEnv.NEXT_TELEMETRY_DISABLED = "1";
buildEnv.PERSONALATTICE_PUBLIC_DEMO_ONLY = "true";
// Keep the public artifact independent of the private API even when a provider
// injects this variable globally into every build environment.
buildEnv.NEXT_PUBLIC_API_URL = "";

const result = spawnSync(process.execPath, [nextBin, "build"], {
  cwd: process.cwd(),
  env: buildEnv,
  stdio: "inherit",
});

if (result.error) throw result.error;
if ((result.status ?? 1) !== 0) process.exit(result.status ?? 1);

const out = path.join(process.cwd(), "out");
const adminDir = path.join(out, "admin");
const adminHtml = path.join(adminDir, "index.html");

function staticAssetRefs(html) {
  const refs = new Set();
  for (const match of html.matchAll(/(?:src|href)=["']\/?(_next\/static\/[^"']+)["']/g)) {
    refs.add(match[1]);
  }
  return refs;
}

function htmlFiles(directory) {
  const files = [];
  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    const absolute = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      if (absolute === adminDir) continue;
      files.push(...htmlFiles(absolute));
      continue;
    }
    if (entry.isFile() && entry.name.endsWith(".html")) files.push(absolute);
  }
  return files;
}

// Next can change the physical naming/layout of route chunks between versions.
// Use the generated route references as the authority instead of assuming that
// private admin assets always live under `_next/static/chunks/app/admin/`.
if (existsSync(adminHtml)) {
  const adminRefs = staticAssetRefs(readFileSync(adminHtml, "utf8"));
  const publicRefs = new Set();
  for (const file of htmlFiles(out)) {
    for (const ref of staticAssetRefs(readFileSync(file, "utf8"))) publicRefs.add(ref);
  }

  for (const ref of adminRefs) {
    if (publicRefs.has(ref)) continue;
    const target = path.resolve(out, ref);
    const staticRoot = path.resolve(out, "_next", "static") + path.sep;
    if (!target.startsWith(staticRoot)) {
      throw new Error(`refusing to remove non-static admin asset: ${ref}`);
    }
    rmSync(target, { force: true });
  }
}

// The public artifact must not merely redirect away from the operator route;
// it must not ship the private operator page or any legacy nested route bundle.
rmSync(adminDir, { recursive: true, force: true });
rmSync(path.join(out, "_next", "static", "chunks", "app", "admin"), {
  recursive: true,
  force: true,
});
