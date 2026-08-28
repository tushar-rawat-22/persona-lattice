import { spawnSync } from "node:child_process";
import { rmSync } from "node:fs";
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
// The public artifact must not merely redirect away from the operator route;
// it must not ship the private operator page or its route-specific bundle.
rmSync(path.join(out, "admin"), { recursive: true, force: true });
rmSync(path.join(out, "_next", "static", "chunks", "app", "admin"), {
  recursive: true,
  force: true,
});
