// @vitest-environment jsdom

import { fireEvent, render, screen, waitFor, cleanup } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import FlowerAssistant from "./FlowerAssistant";
import { askFlowerAdvice, fetchAssistantCapabilities } from "@/lib/api";

vi.mock("@/lib/api", () => ({
  askFlowerAdvice: vi.fn(),
  fetchAssistantCapabilities: vi.fn(),
}));
vi.mock("@/lib/store", () => ({
  useStore: () => ({ user: { id: 1 }, hydrated: true, language: "EN" }),
}));

beforeEach(() => vi.resetAllMocks());
afterEach(cleanup);

it("does not offer AI requests when credentials are not configured", async () => {
  vi.mocked(fetchAssistantCapabilities).mockResolvedValue({
    enabled: false,
    web_search_enabled: false,
  });
  render(<FlowerAssistant />);
  expect(await screen.findByText(/flower helper is not available yet/i)).toBeTruthy();
  expect(screen.queryByRole("textbox")).toBeNull();
  expect(askFlowerAdvice).not.toHaveBeenCalled();
});

it("keeps web search opt-in and displays advice as text, not HTML", async () => {
  vi.mocked(fetchAssistantCapabilities).mockResolvedValue({
    enabled: true,
    web_search_enabled: true,
  });
  vi.mocked(askFlowerAdvice).mockResolvedValue({
    answer: '<img src="x" onerror="alert(1)">',
    sources: [{ title: "Unsafe", url: "javascript:alert(1)" }],
  });
  render(<FlowerAssistant />);
  const input = await screen.findByRole("textbox", { name: "Your question" });
  fireEvent.change(input, { target: { value: "  Birthday roses?  " } });
  expect((screen.getByRole("checkbox") as HTMLInputElement).checked).toBe(false);
  fireEvent.click(screen.getByRole("button", { name: "Ask the flower helper" }));
  await waitFor(() =>
    expect(askFlowerAdvice).toHaveBeenCalledWith({
      message: "Birthday roses?",
      language: "EN",
      use_web_search: false,
    }),
  );
  expect(await screen.findByText('<img src="x" onerror="alert(1)">')).toBeTruthy();
  expect(screen.queryByRole("img")).toBeNull();
  expect(screen.queryByRole("link", { name: "Unsafe" })).toBeNull();
  fireEvent.click(screen.getByRole("checkbox"));
  fireEvent.click(screen.getByRole("button", { name: "Ask the flower helper" }));
  await waitFor(() =>
    expect(askFlowerAdvice).toHaveBeenLastCalledWith({
      message: "Birthday roses?",
      language: "EN",
      use_web_search: true,
    }),
  );
});

it("recovers from a failed advice request without losing the question", async () => {
  vi.mocked(fetchAssistantCapabilities).mockResolvedValue({
    enabled: true,
    web_search_enabled: false,
  });
  vi.mocked(askFlowerAdvice)
    .mockRejectedValueOnce(new Error("private-provider-details"))
    .mockResolvedValueOnce({ answer: "Try roses.", sources: [] });
  render(<FlowerAssistant />);
  const input = await screen.findByRole("textbox", { name: "Your question" });
  fireEvent.change(input, { target: { value: "Roses?" } });
  fireEvent.click(screen.getByRole("button", { name: "Ask the flower helper" }));
  expect(await screen.findByRole("alert")).toHaveProperty(
    "textContent",
    "We couldn't get flower advice. Please try again, or contact support.",
  );
  fireEvent.click(screen.getByRole("button", { name: "Ask the flower helper" }));
  expect(await screen.findByText("Try roses.")).toBeTruthy();
  expect((input as HTMLTextAreaElement).value).toBe("Roses?");
});
