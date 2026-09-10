// @vitest-environment jsdom

import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import SocialLoginButtons from "./SocialLoginButtons";

const fetchOAuthProviders = vi.fn();

vi.mock("@/lib/api", () => ({
  fetchOAuthProviders: () => fetchOAuthProviders(),
  oauthStartUrl: (provider: string) => `https://api.example/oauth/${provider}`,
}));

describe("SocialLoginButtons", () => {
  afterEach(cleanup);

  beforeEach(() => {
    fetchOAuthProviders.mockResolvedValue([
      { id: "google", enabled: true },
      { id: "github", enabled: true },
      { id: "microsoft", enabled: false },
    ]);
  });

  it("renders accessible provider actions and capability state", async () => {
    render(<SocialLoginButtons onNavigate={() => undefined} />);
    expect(screen.getByRole("button", { name: /continue with google/i })).toBeDisabled();
    await waitFor(() =>
      expect(screen.getByRole("button", { name: /continue with google/i })).toBeEnabled(),
    );
    await waitFor(() =>
      expect(screen.getByRole("button", { name: /continue with microsoft/i })).toBeDisabled(),
    );
  });

  it("starts the selected provider flow once", async () => {
    const onNavigate = vi.fn();
    render(<SocialLoginButtons onNavigate={onNavigate} />);
    await waitFor(() => expect(fetchOAuthProviders).toHaveBeenCalled());
    fireEvent.click(screen.getByRole("button", { name: /continue with github/i }));
    expect(onNavigate).toHaveBeenCalledWith("github");
    expect(screen.getByRole("button", { name: /opening provider/i })).toBeDisabled();
  });
});
