import { describe, expect, it } from "vitest";
import { formatPrice, toUzs } from "./currency";

describe("payment amount display", () => {
  it("uses the backend conversion rate without rounding to thousands", () => {
    expect(toUzs(42, 12650)).toBe(531300);
    expect(formatPrice(42, "UZS", 12650)).toBe("531 300 so'm");
    expect(formatPrice(42, "UZS", 12750.5)).toBe("535 521 so'm");
  });

  it("preserves cents in the catalog price unit", () => {
    expect(formatPrice(42.5, "USD")).toBe("$42.5");
  });
});
