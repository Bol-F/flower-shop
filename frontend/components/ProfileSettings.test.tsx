// @vitest-environment jsdom

import "@testing-library/jest-dom/vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fallbackCatalogProducts } from "@/lib/catalog";
import type { Product } from "@/lib/types";
import ProfileSettings from "./ProfileSettings";

const mocks = vi.hoisted(() => ({
  store: {} as Record<string, unknown>,
  fetchOrders: vi.fn(),
  fetchOAuthProviders: vi.fn(),
  fetchProducts: vi.fn(),
}));

vi.mock("next/navigation", () => ({ useRouter: () => ({ refresh: vi.fn() }) }));
vi.mock("@/lib/store", () => ({
  useStore: () => mocks.store,
  usePriceFormatter: () => (amount: number, currency: string) => `${currency} ${amount}`,
}));
vi.mock("@/lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/lib/api")>()),
  fetchOrders: mocks.fetchOrders,
  fetchOAuthProviders: mocks.fetchOAuthProviders,
  fetchProducts: mocks.fetchProducts,
}));
vi.mock("./ProductCard", () => ({
  default: ({ product }: { product: Product }) => (
    <article data-testid="favorite-product" data-backend-id={product.backendId}>
      {product.name}: {product.price}
    </article>
  ),
}));

const apiRose: Product = {
  ...fallbackCatalogProducts[0],
  id: "real-api-rose",
  backendId: 741,
  slug: "real-api-rose",
  name: "Real API Rose",
  price: 87,
  source: "api",
};
const apiTulip: Product = {
  ...apiRose,
  id: "real-api-tulip",
  backendId: 742,
  slug: "real-api-tulip",
  name: "Real API Tulip",
  price: 42,
};

describe("profile favorites", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.fetchOrders.mockResolvedValue([]);
    mocks.fetchOAuthProviders.mockResolvedValue([]);
    mocks.store = {
      user: {
        id: 1,
        username: "Customer",
        email: "customer@example.test",
        is_staff: false,
        loyalty_points: 0,
        city: "Tashkent",
        currency: "USD",
        language: "EN",
        phone: "",
        address: "",
        bio: "",
        date_joined: "2026-10-19",
      },
      name: "Customer",
      city: "Tashkent",
      currency: "USD",
      language: "EN",
      paymentRate: 13000,
      favorites: [],
      favoriteProducts: {},
      setUser: vi.fn(),
      signOut: vi.fn(),
      setName: vi.fn(),
      setCity: vi.fn(),
      setCurrency: vi.fn(),
      setLanguage: vi.fn(),
      showToast: vi.fn(),
      reloadCart: vi.fn(),
    };
  });

  afterEach(cleanup);

  async function settleProfile() {
    await waitFor(() => expect(screen.getByText("No orders yet")).toBeInTheDocument());
  }

  it("renders real saved API products in favorites order without fetching the catalog", async () => {
    mocks.store.favorites = [apiTulip.id, apiRose.id];
    mocks.store.favoriteProducts = { [apiRose.id]: apiRose, [apiTulip.id]: apiTulip };
    render(<ProfileSettings />);
    await settleProfile();

    expect(screen.queryByText("No favorites yet")).not.toBeInTheDocument();
    const cards = screen.getAllByTestId("favorite-product");
    expect(cards.map((card) => card.textContent)).toEqual([
      "Real API Tulip: 42",
      "Real API Rose: 87",
    ]);
    expect(cards[0]).toHaveAttribute("data-backend-id", "742");
    expect(mocks.fetchProducts).not.toHaveBeenCalled();
  });

  it("prefers a real API snapshot over a matching demo product", async () => {
    const demo = fallbackCatalogProducts[0];
    mocks.store.favorites = [demo.id];
    mocks.store.favoriteProducts = { [demo.id]: { ...apiRose, id: demo.id } };
    render(<ProfileSettings />);
    await settleProfile();

    expect(screen.getByTestId("favorite-product")).toHaveTextContent("Real API Rose: 87");
    expect(screen.getByTestId("favorite-product")).toHaveAttribute("data-backend-id", "741");
  });

  it("retains legacy offline favorites and ignores unresolvable ids", async () => {
    const demo = fallbackCatalogProducts[0];
    mocks.store.favorites = ["unknown-product-id", demo.id];
    render(<ProfileSettings />);
    await settleProfile();

    expect(screen.getAllByTestId("favorite-product")).toHaveLength(1);
    expect(screen.getByTestId("favorite-product")).toHaveTextContent(demo.name);
  });

  it("removes an unfavorited product immediately even when its snapshot remains cached", async () => {
    mocks.store.favorites = [apiRose.id];
    mocks.store.favoriteProducts = { [apiRose.id]: apiRose };
    const { rerender } = render(<ProfileSettings />);
    await settleProfile();
    expect(screen.getByTestId("favorite-product")).toHaveTextContent(apiRose.name);

    mocks.store.favorites = [];
    rerender(<ProfileSettings />);
    expect(screen.getByText("No favorites yet")).toBeInTheDocument();
    expect(screen.queryByTestId("favorite-product")).not.toBeInTheDocument();
  });
});
