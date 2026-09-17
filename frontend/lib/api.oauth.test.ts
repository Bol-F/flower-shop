// @vitest-environment jsdom

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, completeOAuthLink, fetchProfile } from "./api";

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

  it("uses one refresh request for parallel 401 responses", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      const headers = init?.headers as Record<string, string> | undefined;
      if (url.endsWith("/api/auth/token/refresh/")) {
        return jsonResponse(200, { access: "new-access", refresh: "new-refresh" });
      }
      if (headers?.Authorization === "Bearer old-access") {
        return jsonResponse(401, { detail: "expired" });
      }
      return jsonResponse(200, refreshedUser);
    });
    vi.stubGlobal("fetch", fetchMock);

    const [first, second] = await Promise.all([fetchProfile(), fetchProfile()]);

    expect(first).toEqual(refreshedUser);
    expect(second).toEqual(refreshedUser);
    const refreshCalls = fetchMock.mock.calls.filter(([url]) =>
      String(url).endsWith("/api/auth/token/refresh/"),
    );
    expect(refreshCalls).toHaveLength(1);
    expect(JSON.parse(String(refreshCalls[0][1]?.body))).toEqual({ refresh: "old-refresh" });
  });

  it.each([429, 503])("preserves auth when refresh fails transiently with %s", async (status) => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce(jsonResponse(401, { detail: "expired" }))
        .mockResolvedValueOnce(jsonResponse(status, { detail: "try later" })),
    );

    await expect(fetchProfile()).rejects.toMatchObject({ status });
    expect(JSON.parse(localStorage.getItem(authKey) ?? "null")).toMatchObject({
      access: "old-access",
      refresh: "old-refresh",
    });
  });

  it("clears auth only when the refresh token itself is invalid", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce(jsonResponse(401, { detail: "expired" }))
        .mockResolvedValueOnce(jsonResponse(401, { detail: "token_not_valid" })),
    );

    await expect(fetchProfile()).rejects.toBeInstanceOf(ApiError);
    expect(localStorage.getItem(authKey)).toBeNull();
  });

  it("does not clear a different account after a late refresh failure", async () => {
    const replacement = {
      access: "other-access",
      refresh: "other-refresh",
      user: { ...originalUser, id: 9, email: "other@example.com" },
    };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(401, { detail: "expired" }))
      .mockImplementationOnce(async () => {
        localStorage.setItem(authKey, JSON.stringify(replacement));
        return jsonResponse(401, { detail: "token_not_valid" });
      });
    vi.stubGlobal("fetch", fetchMock);

    await expect(fetchProfile()).rejects.toBeInstanceOf(ApiError);
    expect(JSON.parse(localStorage.getItem(authKey) ?? "null")).toEqual(replacement);
  });

  it("preserves auth when a successful refresh response is malformed", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce(jsonResponse(401, { detail: "expired" }))
        .mockResolvedValueOnce(jsonResponse(200, { refresh: "missing-access" })),
    );

    await expect(fetchProfile()).rejects.toMatchObject({ status: 502 });
    expect(JSON.parse(localStorage.getItem(authKey) ?? "null")).toMatchObject({
      access: "old-access",
      refresh: "old-refresh",
    });
  });

  it("updates the linked user while preserving the current JWT pair", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, { user: refreshedUser }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(completeOAuthLink("one-time-link-code")).resolves.toEqual(refreshedUser);

    expect(JSON.parse(localStorage.getItem(authKey) ?? "null")).toEqual({
      access: "old-access",
      refresh: "old-refresh",
      user: refreshedUser,
    });
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/auth/oauth/link/exchange/"),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ code: "one-time-link-code" }),
        headers: expect.objectContaining({ Authorization: "Bearer old-access" }),
      }),
    );
  });
});
