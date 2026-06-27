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
};

export default nextConfig;
