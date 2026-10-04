import type { NextConfig } from "next";
import os from "node:os";

const configuredDevOrigins = (process.env.NEXT_ALLOWED_DEV_ORIGINS ?? "")
  .split(",")
  .map((origin) => origin.trim())
  .filter(Boolean);

const localDevOrigins = Object.values(os.networkInterfaces()).flatMap((addresses = []) =>
  addresses
    .filter((address) => address.family === "IPv4" && !address.internal)
    .map((address) => address.address),
);

const apiOrigin = (() => {
  try {
    const url = new URL(process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000");
    const local = url.hostname === "localhost" || url.hostname === "127.0.0.1";
    if (process.env.NODE_ENV === "production" && url.protocol !== "https:" && !local) {
      throw new Error("Production NEXT_PUBLIC_API_URL must use HTTPS.");
    }
    return url.origin;
  } catch {
    if (process.env.NEXT_PUBLIC_API_URL) {
      throw new Error("NEXT_PUBLIC_API_URL must be an HTTPS origin in production.");
    }
    return "http://localhost:8000";
  }
})();

const contentSecurityPolicy = [
  "default-src 'self'",
  "base-uri 'self'",
  "frame-ancestors 'none'",
  "form-action 'self'",
  "object-src 'none'",
  `script-src 'self' 'unsafe-inline'${
    process.env.NODE_ENV === "production" ? "" : " 'unsafe-eval'"
  }`,
  "style-src 'self' 'unsafe-inline'",
  "font-src 'self' data:",
  `img-src 'self' data: blob: https: ${apiOrigin}`,
  `connect-src 'self' ${apiOrigin} https: ws: wss:`,
  ...(process.env.NODE_ENV === "production" ? ["upgrade-insecure-requests"] : []),
].join("; ");

const nextConfig: NextConfig = {
  allowedDevOrigins: [...new Set([...configuredDevOrigins, ...localDevOrigins])],
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "Content-Security-Policy", value: contentSecurityPolicy },
          {
            key: "Permissions-Policy",
            value: "camera=(), microphone=(), payment=(), usb=()",
          },
        ],
      },
    ];
  },
};

export default nextConfig;
