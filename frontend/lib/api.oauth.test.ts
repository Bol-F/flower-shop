// @vitest-environment jsdom

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  ApiError,
  completeOAuth,
  completeOAuthLink,
  fetchProfile,
  login,
  logout,
  mergeGuestSelections,
  register,
  updateProfile,
} from "./api";

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
const replacement = {
  access: "other-access",
  refresh: "other-refresh",
  user: { ...originalUser, id: 9, email: "other@example.com" },
};

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((resolvePromise) => {
    resolve = resolvePromise;
  });
  return { promise, resolve };
}

const userRequests = [
  { name: "profile fetch", run: () => fetchProfile(), response: refreshedUser },
  {
    name: "profile update",
    run: () => updateProfile({ username: "refreshed" }),
    response: refreshedUser,
  },
  {
    name: "OAuth account link",
    run: () => completeOAuthLink("one-time-link-code"),
    response: { user: refreshedUser },
  },
];
const authenticationRequests = [
  { name: "password sign-in", run: () => login("original@example.com", "password") },
  { name: "OAuth sign-in", run: () => completeOAuth("one-time-login-code") },
];

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

  it("reuses the token rotated by another tab while waiting for the browser lock", async () => {
    const requestLock = vi.fn(async (_name: string, callback: () => unknown) => {
      localStorage.setItem(
        authKey,
        JSON.stringify({
          access: "tab-access",
          refresh: "tab-refresh",
          user: originalUser,
        }),
      );
      return callback();
    });
    vi.stubGlobal("navigator", { locks: { request: requestLock } });
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(401, { detail: "expired" }))
      .mockResolvedValueOnce(jsonResponse(200, originalUser));
    vi.stubGlobal("fetch", fetchMock);

    await expect(fetchProfile()).resolves.toEqual(originalUser);
    expect(requestLock).toHaveBeenCalledOnce();
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(fetchMock.mock.calls[1][1].headers.Authorization).toBe("Bearer tab-access");
  });

  it("does not use another account's credentials after waiting for the browser lock", async () => {
    vi.stubGlobal("navigator", {
      locks: {
        request: async (_name: string, callback: () => unknown) => {
          localStorage.setItem(
            authKey,
            JSON.stringify({
              access: "other-access",
              refresh: "other-refresh",
              user: { ...originalUser, id: 9 },
            }),
          );
          return callback();
        },
      },
    });
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(401, { detail: "expired" }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(fetchProfile()).rejects.toMatchObject({
      status: 409,
      details: { code: "auth_changed" },
    });
    expect(fetchMock).toHaveBeenCalledOnce();
    expect(JSON.parse(localStorage.getItem(authKey) ?? "null").user.id).toBe(9);
  });

  describe.each(userRequests)("stale $name responses", ({ run, response }) => {
    it.each(["account switch", "logout"])("discards a response after %s", async (change) => {
      const responseFlight = deferred<Response>();
      const fetchMock = vi.fn().mockReturnValue(responseFlight.promise);
      vi.stubGlobal("fetch", fetchMock);
      const pending = run();
      const rejected = expect(pending).rejects.toMatchObject({
        status: 409,
        details: { code: "auth_changed" },
      });

      if (change === "account switch") {
        localStorage.setItem(authKey, JSON.stringify(replacement));
      } else {
        logout();
      }
      const authChanged = vi.fn();
      window.addEventListener("bloompetal:auth-changed", authChanged);
      responseFlight.resolve(jsonResponse(200, response));
      try {
        await rejected;
        expect(JSON.parse(localStorage.getItem(authKey) ?? "null")).toEqual(
          change === "account switch" ? replacement : null,
        );
        expect(authChanged).not.toHaveBeenCalled();
        expect(fetchMock).toHaveBeenCalledOnce();
      } finally {
        window.removeEventListener("bloompetal:auth-changed", authChanged);
      }
    });

    it("keeps tokens rotated while the user response was loading", async () => {
      const responseFlight = deferred<Response>();
      vi.stubGlobal("fetch", vi.fn().mockReturnValue(responseFlight.promise));
      const pending = run();
      localStorage.setItem(
        authKey,
        JSON.stringify({
          access: "rotated-access",
          refresh: "rotated-refresh",
          user: originalUser,
        }),
      );
      responseFlight.resolve(jsonResponse(200, response));

      await expect(pending).resolves.toEqual(refreshedUser);
      expect(JSON.parse(localStorage.getItem(authKey) ?? "null")).toEqual({
        access: "rotated-access",
        refresh: "rotated-refresh",
        user: refreshedUser,
      });
    });

    it("rejects a user response belonging to an unexpected account", async () => {
      const invalid = "user" in response ? { user: replacement.user } : replacement.user;
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(200, invalid)));

      await expect(run()).rejects.toMatchObject({ status: 502 });
      expect(JSON.parse(localStorage.getItem(authKey) ?? "null")).toEqual({
        access: "old-access",
        refresh: "old-refresh",
        user: originalUser,
      });
    });
  });

  it("discards a profile response if the account switches while decoding its body", async () => {
    const bodyFlight = deferred<typeof refreshedUser>();
    const decoding = deferred<void>();
    const response = jsonResponse(200, {});
    vi.spyOn(response, "json").mockImplementation(() => {
      decoding.resolve();
      return bodyFlight.promise;
    });
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response));
    const pending = fetchProfile();
    const rejected = expect(pending).rejects.toMatchObject({
      status: 409,
      details: { code: "auth_changed" },
    });
    await decoding.promise;
    localStorage.setItem(authKey, JSON.stringify(replacement));
    bodyFlight.resolve(refreshedUser);

    await rejected;
    expect(JSON.parse(localStorage.getItem(authKey) ?? "null")).toEqual(replacement);
  });

  it("does not refresh or retry another account after a delayed 401 response", async () => {
    const responseFlight = deferred<Response>();
    const fetchMock = vi.fn().mockReturnValue(responseFlight.promise);
    vi.stubGlobal("fetch", fetchMock);
    const pending = fetchProfile();
    const rejected = expect(pending).rejects.toMatchObject({ status: 409 });
    localStorage.setItem(authKey, JSON.stringify(replacement));
    responseFlight.resolve(jsonResponse(401, { detail: "expired" }));

    await rejected;
    expect(fetchMock).toHaveBeenCalledOnce();
    expect(fetchMock.mock.calls[0][1].headers.Authorization).toBe("Bearer old-access");
    expect(JSON.parse(localStorage.getItem(authKey) ?? "null")).toEqual(replacement);
  });

  it("discards a late successful response after refreshing the original account", async () => {
    const retryFlight = deferred<Response>();
    const retried = deferred<void>();
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(401, { detail: "expired" }))
      .mockResolvedValueOnce(jsonResponse(200, { access: "new-access", refresh: "new-refresh" }))
      .mockImplementationOnce(() => {
        retried.resolve();
        return retryFlight.promise;
      });
    vi.stubGlobal("fetch", fetchMock);
    const pending = completeOAuthLink("one-time-link-code");
    const rejected = expect(pending).rejects.toMatchObject({ status: 409 });
    await retried.promise;
    localStorage.setItem(authKey, JSON.stringify(replacement));
    retryFlight.resolve(jsonResponse(200, { user: refreshedUser }));

    await rejected;
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(fetchMock.mock.calls[2][1].headers.Authorization).toBe("Bearer new-access");
    expect(JSON.parse(localStorage.getItem(authKey) ?? "null")).toEqual(replacement);
  });

  it("posts an authenticated, idempotent guest-selection merge", async () => {
    const payload = {
      merge_id: "guest-merge-id",
      items: [{ product_slug: "pink-roses", quantity: 2 }],
      wishlist: ["pink-roses"],
    };
    const result = {
      cart: { id: 1, items: [], total_price: "0.00", total_items: 0, updated_at: "" },
      wishlist: [],
      adjusted_products: [],
      unavailable_products: [],
    };
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, result));
    vi.stubGlobal("fetch", fetchMock);

    await expect(mergeGuestSelections(payload)).resolves.toEqual(result);
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/cart/merge/"),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify(payload),
        headers: expect.objectContaining({ Authorization: "Bearer old-access" }),
      }),
    );
  });

  it("discards a guest merge completed after switching accounts", async () => {
    const responseFlight = deferred<Response>();
    vi.stubGlobal("fetch", vi.fn().mockReturnValue(responseFlight.promise));
    const pending = mergeGuestSelections({ merge_id: "guest-merge-id", items: [], wishlist: [] });
    const rejected = expect(pending).rejects.toMatchObject({
      status: 409,
      details: { code: "auth_changed" },
    });
    localStorage.setItem(authKey, JSON.stringify(replacement));
    responseFlight.resolve(jsonResponse(200, { cart: { items: [] }, wishlist: [] }));

    await rejected;
    expect(JSON.parse(localStorage.getItem(authKey) ?? "null")).toEqual(replacement);
  });

  it("retains a 401 response when the active refresh token is invalid", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce(jsonResponse(401, { detail: "expired" }))
        .mockResolvedValueOnce(jsonResponse(401, { detail: "token_not_valid" })),
    );

    await expect(fetchProfile()).rejects.toMatchObject({ status: 401 });
    expect(localStorage.getItem(authKey)).toBeNull();
  });

  describe.each(authenticationRequests)("$name completion", ({ run }) => {
    it("can intentionally replace an unchanged existing account", async () => {
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(200, replacement)));

      await expect(run()).resolves.toEqual(replacement.user);
      expect(JSON.parse(localStorage.getItem(authKey) ?? "null")).toEqual(replacement);
    });

    it("does not overwrite an account switched while the response was pending", async () => {
      const flight = deferred<Response>();
      vi.stubGlobal("fetch", vi.fn().mockReturnValue(flight.promise));
      const pending = run();
      const rejected = expect(pending).rejects.toMatchObject({
        status: 409,
        details: { code: "auth_changed" },
      });
      localStorage.setItem(authKey, JSON.stringify(replacement));
      flight.resolve(
        jsonResponse(200, {
          access: "late-access",
          refresh: "late-refresh",
          user: originalUser,
        }),
      );

      await rejected;
      expect(JSON.parse(localStorage.getItem(authKey) ?? "null")).toEqual(replacement);
    });

    it("does not sign in after logout, even when the request began signed out", async () => {
      localStorage.clear();
      const flight = deferred<Response>();
      vi.stubGlobal("fetch", vi.fn().mockReturnValue(flight.promise));
      const pending = run();
      const rejected = expect(pending).rejects.toMatchObject({ status: 409 });
      logout();
      flight.resolve(jsonResponse(200, replacement));

      await rejected;
      expect(localStorage.getItem(authKey)).toBeNull();
    });

    it.each([null, [], {}, { access: "a", refresh: "r", user: null }])(
      "rejects malformed successful sign-in responses without changing the session: %j",
      async (response) => {
        vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(200, response)));

        await expect(run()).rejects.toMatchObject({ status: 502 });
        expect(JSON.parse(localStorage.getItem(authKey) ?? "null")).toEqual({
          access: "old-access",
          refresh: "old-refresh",
          user: originalUser,
        });
      },
    );
  });

  it("does not let an older sign-in overwrite a more recently completed sign-in", async () => {
    const firstFlight = deferred<Response>();
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockReturnValueOnce(firstFlight.promise)
        .mockResolvedValueOnce(jsonResponse(200, replacement)),
    );
    const pending = completeOAuth("older-code");
    const rejected = expect(pending).rejects.toMatchObject({ status: 409 });
    await login("other@example.com", "password");
    firstFlight.resolve(
      jsonResponse(200, {
        access: "late-access",
        refresh: "late-refresh",
        user: originalUser,
      }),
    );

    await rejected;
    expect(JSON.parse(localStorage.getItem(authKey) ?? "null")).toEqual(replacement);
  });

  it("rejects an old profile response after logout and a fresh sign-in to the same account", async () => {
    const profileFlight = deferred<Response>();
    const signedInAgain = { access: "fresh-access", refresh: "fresh-refresh", user: originalUser };
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockReturnValueOnce(profileFlight.promise)
        .mockResolvedValueOnce(jsonResponse(200, signedInAgain)),
    );
    const pending = fetchProfile();
    const rejected = expect(pending).rejects.toMatchObject({ status: 409 });
    logout();
    await login("original@example.com", "password");
    profileFlight.resolve(jsonResponse(200, refreshedUser));

    await rejected;
    expect(JSON.parse(localStorage.getItem(authKey) ?? "null")).toEqual(signedInAgain);
  });

  it("does not automatically sign in after registration if the session changed", async () => {
    const registrationFlight = deferred<Response>();
    const fetchMock = vi.fn().mockReturnValue(registrationFlight.promise);
    vi.stubGlobal("fetch", fetchMock);
    const pending = register({
      username: "new-customer",
      email: "new-customer@example.test",
      password: "password",
      password_confirm: "password",
    });
    const rejected = expect(pending).rejects.toMatchObject({ status: 409 });
    localStorage.setItem(authKey, JSON.stringify(replacement));
    registrationFlight.resolve(jsonResponse(201, { ...originalUser, id: 18 }));

    await rejected;
    expect(fetchMock).toHaveBeenCalledOnce();
    expect(JSON.parse(localStorage.getItem(authKey) ?? "null")).toEqual(replacement);
  });

  it("allows OAuth completion after an ordinary token rotation of the original session", async () => {
    const oauthFlight = deferred<Response>();
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockReturnValueOnce(oauthFlight.promise)
        .mockResolvedValueOnce(jsonResponse(401, { detail: "expired" }))
        .mockResolvedValueOnce(
          jsonResponse(200, { access: "rotated-access", refresh: "rotated-refresh" }),
        )
        .mockResolvedValueOnce(jsonResponse(200, refreshedUser)),
    );
    const pending = completeOAuth("replacement-login-code");
    await expect(fetchProfile()).resolves.toEqual(refreshedUser);
    oauthFlight.resolve(jsonResponse(200, replacement));

    await expect(pending).resolves.toEqual(replacement.user);
    expect(JSON.parse(localStorage.getItem(authKey) ?? "null")).toEqual(replacement);
  });

  it.each(["null", "[]", '{"access":1}', '{"access":"a","refresh":"r","user":null}'])(
    "ignores malformed stored credentials: %s",
    async (stored) => {
      localStorage.setItem(authKey, stored);
      const fetchMock = vi.fn().mockResolvedValue(jsonResponse(401, null));
      vi.stubGlobal("fetch", fetchMock);
      await expect(fetchProfile()).rejects.toBeInstanceOf(ApiError);
      expect(fetchMock).toHaveBeenCalledOnce();
      expect(fetchMock.mock.calls[0][1].headers.Authorization).toBeUndefined();
    },
  );
});
