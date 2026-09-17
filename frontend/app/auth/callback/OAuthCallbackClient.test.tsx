// @vitest-environment jsdom

import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ComponentProps } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { OfflineError } from "@/lib/api";
import OAuthCallbackClient from "./OAuthCallbackClient";

const mocks = vi.hoisted(() => ({
  completeOAuth: vi.fn(),
  completeOAuthLink: vi.fn(),
  replace: vi.fn(),
  setName: vi.fn(),
  setUser: vi.fn(),
  showToast: vi.fn(),
}));

vi.mock("next/navigation", () => ({ useRouter: () => ({ replace: mocks.replace }) }));
vi.mock("@/lib/store", () => ({
  useStore: () => ({
    setUser: mocks.setUser,
    setName: mocks.setName,
    showToast: mocks.showToast,
  }),
}));
vi.mock("@/lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/lib/api")>()),
  completeOAuth: mocks.completeOAuth,
  completeOAuthLink: mocks.completeOAuthLink,
}));

const user = {
  id: 7,
  username: "Petal Friend",
  email: "friend@example.com",
};

const defaultProps: ComponentProps<typeof OAuthCallbackClient> = {
  error: "",
  flow: "",
  message: "",
};

function renderCallback(overrides: Partial<ComponentProps<typeof OAuthCallbackClient>> = {}) {
  return render(<OAuthCallbackClient {...defaultProps} {...overrides} />);
}

describe("OAuthCallbackClient", () => {
  beforeEach(() => {
    window.history.replaceState(null, "", "/auth/callback");
    vi.clearAllMocks();
    mocks.completeOAuth.mockResolvedValue(user);
    mocks.completeOAuthLink.mockResolvedValue(user);
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("shows a safe cancellation error and a retry link", () => {
    renderCallback({ error: "cancelled", message: "Sign-in was cancelled." });
    expect(screen.getByRole("alert")).toHaveTextContent("Sign-in was cancelled.");
    expect(screen.getByRole("link", { name: /return to sign in/i })).toHaveAttribute(
      "href",
      "/profile?mode=login",
    );
  });

  it("strips a fragment code before exchanging it and completes sign-in", async () => {
    window.history.replaceState(
      null,
      "",
      "/auth/callback#code=one-time-login&next=%2Forders%3Fview%3Dcurrent",
    );
    const replaceState = vi.spyOn(window.history, "replaceState");

    renderCallback();

    await waitFor(() => expect(mocks.completeOAuth).toHaveBeenCalledWith("one-time-login"));
    expect(replaceState).toHaveBeenCalledWith(null, "", "/auth/callback");
    expect(replaceState.mock.invocationCallOrder[0]).toBeLessThan(
      mocks.completeOAuth.mock.invocationCallOrder[0],
    );
    expect(window.location.hash).toBe("");
    expect(mocks.setUser).toHaveBeenCalledWith(user);
    expect(mocks.setName).toHaveBeenCalledWith("Petal Friend");
    expect(mocks.replace).toHaveBeenCalledWith("/orders?view=current");
  });

  it("never accepts a one-time exchange code from the query string", async () => {
    window.history.replaceState(null, "", "/auth/callback?code=leaked-query-code");
    renderCallback();

    expect(await screen.findByRole("alert")).toHaveTextContent("did not include one usable code");
    expect(mocks.completeOAuth).not.toHaveBeenCalled();
  });

  it("exchanges an account-link fragment without replacing existing login tokens", async () => {
    window.history.replaceState(
      null,
      "",
      "/auth/callback#link_code=one-time-link&provider=google&next=%2Fprofile",
    );

    renderCallback();

    await waitFor(() => expect(mocks.completeOAuthLink).toHaveBeenCalledWith("one-time-link"));
    expect(mocks.completeOAuth).not.toHaveBeenCalled();
    expect(mocks.setUser).toHaveBeenCalledWith(user);
    expect(mocks.showToast).toHaveBeenCalledWith("Google is now connected.");
    expect(mocks.replace).toHaveBeenCalledWith("/profile");
  });

  it("shows a recoverable error when the one-time exchange fails", async () => {
    mocks.completeOAuth.mockRejectedValueOnce(new Error("This sign-in link has expired."));
    window.history.replaceState(null, "", "/auth/callback#code=expired-code");

    renderCallback();

    expect(await screen.findByRole("alert")).toHaveTextContent("This sign-in link has expired.");
    expect(screen.getByRole("link", { name: /return to sign in/i })).toBeVisible();
  });

  it("retries a transient exchange from in-memory credentials only", async () => {
    mocks.completeOAuth.mockRejectedValueOnce(new OfflineError()).mockResolvedValueOnce(user);
    window.history.replaceState(
      null,
      "",
      "/auth/callback#code=retry-code&next=%2Fprofile%3Ftab%3Dsecurity",
    );

    renderCallback();

    const retry = await screen.findByRole("button", { name: /try exchange again/i });
    expect(window.location.hash).toBe("");
    fireEvent.click(retry);
    await waitFor(() => expect(mocks.completeOAuth).toHaveBeenCalledTimes(2));
    expect(mocks.completeOAuth).toHaveBeenLastCalledWith("retry-code");
    expect(mocks.replace).toHaveBeenCalledWith("/profile?tab=security");
  });

  it("keeps encoded slashes inside same-origin query values", async () => {
    window.history.replaceState(
      null,
      "",
      "/auth/callback#code=safe-code&next=%2Fsearch%3Fq%3Da%252Fb",
    );

    renderCallback();

    await waitFor(() => expect(mocks.completeOAuth).toHaveBeenCalledWith("safe-code"));
    expect(mocks.replace).toHaveBeenCalledWith("/search?q=a%2Fb");
  });

  it("shows a recoverable error when the callback has no code", async () => {
    renderCallback();

    expect(await screen.findByRole("alert")).toHaveTextContent("did not include one usable code");
    expect(mocks.completeOAuth).not.toHaveBeenCalled();
    expect(mocks.completeOAuthLink).not.toHaveBeenCalled();
  });

  it.each([
    "//evil.example/steal",
    "/\\evil.example/steal",
    "javascript:alert(1)",
    "/%5cevil.example/steal",
    "/orders%0d%0aSet-Cookie:bad",
  ])("rejects an unsafe next destination: %s", async (unsafeNext) => {
    window.history.replaceState(
      null,
      "",
      `/auth/callback#code=safe-code&next=${encodeURIComponent(unsafeNext)}`,
    );

    renderCallback();

    await waitFor(() => expect(mocks.completeOAuth).toHaveBeenCalledWith("safe-code"));
    expect(mocks.replace).toHaveBeenCalledWith("/profile");
  });
});
