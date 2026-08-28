import type { NextConfig } from "next";

const publicDemoOnly = process.env.PERSONALATTICE_PUBLIC_DEMO_ONLY === "true";
const apiOrigin =
  process.env.PERSONALATTICE_API_ORIGIN ??
  (process.env.PERSONALATTICE_API_HOSTPORT
    ? `http://${process.env.PERSONALATTICE_API_HOSTPORT}`
    : "http://127.0.0.1:8000");

const securityHeaders = [
  {
    key: "Content-Security-Policy",
    value: "base-uri 'self'; form-action 'self'; frame-ancestors 'none'; object-src 'none'",
  },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Referrer-Policy", value: "no-referrer" },
  {
    key: "Permissions-Policy",
    value: "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
  },
  {
    key: "Strict-Transport-Security",
    value: "max-age=31536000; includeSubDomains",
  },
];

const nextConfig: NextConfig = {
  ...(publicDemoOnly ? { output: "export" as const, trailingSlash: true } : {}),
  allowedDevOrigins: ["127.0.0.1"],
  env: {
    // The public static build has no API authority. The private runtime stays same-origin through /api.
    NEXT_PUBLIC_API_URL: publicDemoOnly ? "/__public_demo_no_api__" : "/api",
  },
  turbopack: {
    root: process.cwd(),
  },
  ...(publicDemoOnly
    ? {}
    : {
        async headers() {
          return [
            {
              source: "/(.*)",
              headers: securityHeaders,
            },
          ];
        },
        async rewrites() {
          return [
            {
              source: "/api/:path*",
              destination: `${apiOrigin}/:path*`,
            },
          ];
        },
      }),
};

export default nextConfig;
