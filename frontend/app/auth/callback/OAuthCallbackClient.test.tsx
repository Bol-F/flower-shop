// @vitest-environment jsdom

import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import OAuthCallbackClient from "./OAuthCallbackClient";

vi.mock("next/navigation", () => ({ useRouter: () => ({ replace: vi.fn() }) }));
vi.mock("@/lib/store", () => ({
  useStore: () => ({ setUser: vi.fn(), setName: vi.fn(), showToast: vi.fn() }),
}));
vi.mock("@/lib/api", () => ({ completeOAuth: vi.fn() }));

describe("OAuthCallbackClient", () => {
  it("shows a safe cancellation error and a retry link", () => {
    render(
      <OAuthCallbackClient
        code=""
        error="cancelled"
        message="Sign-in was cancelled."
        next="/profile"
      />,
    );
    expect(screen.getByRole("alert")).toHaveTextContent("Sign-in was cancelled.");
    expect(screen.getByRole("link", { name: /return to sign in/i })).toHaveAttribute(
      "href",
      "/profile?mode=login",
    );
  });
});
