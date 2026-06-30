import type { NextConfig } from "next";
import os from "node:os";

const configuredDevOrigins = (process.env.NEXT_ALLOWED_DEV_ORIGINS ?? "")
  .split(",")
  .map((origin) => origin.trim())
  .filter(Boolean);

const localDevOrigins = Object.values(os.networkInterfaces()).flatMap(
  (addresses = []) =>
    addresses
      .filter((address) => address.family === "IPv4" && !address.internal)
      .map((address) => address.address),
);

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
