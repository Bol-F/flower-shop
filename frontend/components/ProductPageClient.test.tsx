// @vitest-environment jsdom
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { ApiError } from "@/lib/api";
import { loadCatalogProduct } from "@/lib/catalog";
import { products } from "@/lib/data";
import ProductPageClient from "./ProductPageClient";

vi.mock("@/lib/catalog", () => ({ loadCatalogProduct: vi.fn(), fallbackProduct: vi.fn() }));
vi.mock("./ProductDetail", () => ({
  default: ({ product }: { product: { name: string; price: number; stock: number } }) => (
    <p>
      {product.name}: {product.price}, stock {product.stock}
    </p>
  ),
}));
afterEach(() => {
  cleanup();
  vi.resetAllMocks();
});

it("refreshes server-provided API prices and availability, including on focus", async () => {
  const initial = { ...products[0], source: "api" as const, name: "Rose", price: 10, stock: 5 };
  vi.mocked(loadCatalogProduct)
    .mockResolvedValueOnce({ ...initial, price: 15, stock: 3 })
    .mockResolvedValueOnce({ ...initial, price: 20, stock: 0 });
  render(<ProductPageClient id="rose" initialProduct={initial} />);
  expect(await screen.findByText("Rose: 15, stock 3")).toBeTruthy();
  fireEvent.focus(window);
  expect(await screen.findByText("Rose: 20, stock 0")).toBeTruthy();
});

it("removes an API product that was deleted instead of rendering an old sale", async () => {
  vi.mocked(loadCatalogProduct).mockRejectedValue(new ApiError(404, { detail: "Not found" }));
  render(<ProductPageClient id="deleted" initialProduct={{ ...products[0], source: "api" }} />);
  expect(await screen.findByText("This product is unavailable")).toBeTruthy();
});

it("keeps the last known product with a clear refresh warning while offline", async () => {
  vi.mocked(loadCatalogProduct).mockRejectedValue(new Error("offline"));
  render(<ProductPageClient id="rose" initialProduct={{ ...products[0], source: "api" }} />);
  await waitFor(() =>
    expect(screen.getByRole("status").textContent).toContain("Checkout will confirm"),
  );
});

it("does not let an older refresh overwrite a newer price", async () => {
  const initial = { ...products[0], source: "api" as const, name: "Rose", price: 10, stock: 5 };
  let resolveOlder!: (value: typeof initial) => void;
  vi.mocked(loadCatalogProduct)
    .mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          resolveOlder = resolve;
        }),
    )
    .mockResolvedValueOnce({ ...initial, price: 20, stock: 1 });
  render(<ProductPageClient id="rose" initialProduct={initial} />);
  fireEvent.focus(window);
  expect(await screen.findByText("Rose: 20, stock 1")).toBeTruthy();
  await act(async () => {
    resolveOlder({ ...initial, price: 15, stock: 3 });
  });
  expect(screen.getByText("Rose: 20, stock 1")).toBeTruthy();
});
