// @vitest-environment jsdom

import "@testing-library/jest-dom/vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { Language } from "@/lib/types";
import Footer from "./Footer";

const mocks = vi.hoisted(() => ({ language: "EN" as Language }));

vi.mock("next/navigation", () => ({ usePathname: () => "/" }));
vi.mock("@/lib/store", () => ({ useStore: () => ({ language: mocks.language }) }));

describe("public footer contact", () => {
  afterEach(cleanup);

  it.each([
    ["EN", "Contact support on Telegram"],
    ["RU", "Написать в поддержку в Telegram"],
    ["UZ", "Telegram orqali yordam xizmatiga yozish"],
  ] as const)(
    "provides the existing support channel in %s without unverified phone or hours",
    (language, label) => {
      mocks.language = language;
      const { container } = render(<Footer />);

      expect(screen.getByRole("link", { name: label })).toHaveAttribute(
        "href",
        "https://t.me/Bol_F",
      );
      expect(container.querySelector('a[href^="tel:"]')).not.toBeInTheDocument();
      expect(container).not.toHaveTextContent(/123-45-67|8:00|22:00/);
    },
  );
});
