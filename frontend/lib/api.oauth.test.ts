// @vitest-environment jsdom

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { completeOAuthLink, fetchProfile } from "./api";

const authKey = "bloompetal:auth";
const originalUser = {
  id: 1,
  username: "original",
  email: "original@example.com",
};
const refreshedUser = {
  ...originalUser,
  username: "refreshed",
  social_identities: [
    {
      provider: "google",
      email: "original@example.com",
      email_verified: true,
    },
  ],
};

function jsonResponse(status: number, body: unknown) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("OAuth API authentication state", () => {
  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem(
      authKey,
      JSON.stringify({ access: "old-access", refresh: "old-refresh", user: originalUser }),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    localStorage.clear();
  });

  it("keeps SimpleJWT's rotated refresh token after retrying an authenticated request", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(401, { detail: "expired" }))
      .mockResolvedValueOnce(jsonResponse(200, { access: "new-access", refresh: "new-refresh" }))
      .mockResolvedValueOnce(jsonResponse(200, refreshedUser));
    vi.stubGlobal("fetch", fetchMock);

    await expect(fetchProfile()).resolves.toEqual(refreshedUser);

    const stored = JSON.parse(localStorage.getItem(authKey) ?? "null") as {
      access: string;
      refresh: string;
      user: typeof refreshedUser;
    };
    expect(stored).toMatchObject({
      access: "new-access",
      refresh: "new-refresh",
      user: refreshedUser,
    });
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });

  it("updates the linked user while preserving the current JWT pair", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(200, { user: refreshedUser })));

    await expect(completeOAuthLink("one-time-link-code")).resolves.toEqual(refreshedUser);

    expect(JSON.parse(localStorage.getItem(authKey) ?? "null")).toEqual({
      access: "old-access",
      refresh: "old-refresh",
      user: refreshedUser,
    });
  });
});
