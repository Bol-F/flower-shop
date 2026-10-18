// @vitest-environment jsdom

import { StrictMode, type ReactNode } from "react";
import { act, cleanup, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { ApiCart, ApiProductListItem, AuthUser, GuestSelectionMergeResult } from "./api";
import { apiProductToProduct } from "./catalog";
import { StoreProvider, useStore } from "./store";

const mocks = vi.hoisted(() => ({
  auth: null as { user: AuthUser; access: string; refresh: string } | null,
  listeners: new Set<(auth: { user: AuthUser; access: string; refresh: string } | null) => void>(),
  fetchCart: vi.fn(),
  fetchWishlist: vi.fn(),
  merge: vi.fn(),
  addCart: vi.fn(),
  updateCart: vi.fn(),
  removeCart: vi.fn(),
  clearCart: vi.fn(),
  addWishlist: vi.fn(),
  removeWishlist: vi.fn(),
}));

vi.mock("./api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("./api")>()),
  loadAuth: () => mocks.auth,
  subscribeAuth: (listener: (auth: typeof mocks.auth) => void) => {
    mocks.listeners.add(listener);
    return () => mocks.listeners.delete(listener);
  },
  logout: () => changeAuth(null),
  fetchPaymentConfiguration: async () => ({ uzs_per_price_unit: "13000" }),
  fetchCart: mocks.fetchCart,
  fetchWishlist: mocks.fetchWishlist,
  mergeGuestSelections: mocks.merge,
  addCartItem: mocks.addCart,
  updateCartItem: mocks.updateCart,
  removeCartItem: mocks.removeCart,
  clearRemoteCart: mocks.clearCart,
  addWishlistItem: mocks.addWishlist,
  removeWishlistItem: mocks.removeWishlist,
}));

const user = (id: number): AuthUser => ({
  id,
  username: `customer-${id}`,
  email: `customer-${id}@example.test`,
  phone: "",
  address: "",
  bio: "",
  city: "Tashkent",
  language: "EN",
  currency: "USD",
  loyalty_points: 0,
  is_staff: false,
  date_joined: "2026-10-18",
});

const rose: ApiProductListItem = {
  id: 1,
  slug: "rose",
  name: "Rose",
  price: "20.00",
  image: null,
  category: null,
  category_name: "Flowers",
  city_name: null,
  city_slug: null,
  vendor_name: null,
  vendor_slug: null,
  stock_quantity: 5,
  is_available: true,
  is_in_stock: true,
  is_low_stock: false,
  stock_status: "in_stock",
  rating_average: null,
  rating_count: 0,
  created_at: "2026-01-01",
};
const tulip: ApiProductListItem = { ...rose, id: 2, slug: "tulip", name: "Tulip" };
const roseProduct = apiProductToProduct(rose);
const tulipProduct = apiProductToProduct(tulip);

function cart(...items: Array<[ApiProductListItem, number]>): ApiCart {
  return {
    id: 1,
    items: items.map(([product, quantity], index) => ({
      id: index + 1,
      product,
      quantity,
      subtotal: String(Number(product.price) * quantity),
    })),
    total_price: String(
      items.reduce((sum, [product, quantity]) => sum + Number(product.price) * quantity, 0),
    ),
    total_items: items.reduce((sum, [, quantity]) => sum + quantity, 0),
    updated_at: "2026-10-18",
  };
}

function merged(
  resultCart: ApiCart,
  wishlist: ApiProductListItem[] = [],
): GuestSelectionMergeResult {
  return { cart: resultCart, wishlist, adjusted_products: [], unavailable_products: [] };
}

function changeAuth(next: AuthUser | null) {
  mocks.auth = next
    ? { user: next, access: `access-${next.id}`, refresh: `refresh-${next.id}` }
    : null;
  for (const listener of mocks.listeners) listener(mocks.auth);
}

function deferred<T>() {
  let resolve!: (result: T) => void;
  let reject!: (error: Error) => void;
  const promise = new Promise<T>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
}

function wrapper({ children }: { children: ReactNode }) {
  return (
    <StrictMode>
      <StoreProvider>{children}</StoreProvider>
    </StrictMode>
  );
}

describe("account-scoped cart and favorite synchronization", () => {
  beforeEach(() => {
    localStorage.clear();
    mocks.auth = null;
    mocks.listeners.clear();
    vi.clearAllMocks();
    mocks.fetchCart.mockResolvedValue(cart());
    mocks.fetchWishlist.mockResolvedValue([]);
    mocks.merge.mockResolvedValue(merged(cart()));
    mocks.addCart.mockResolvedValue(cart([rose, 1]));
    mocks.updateCart.mockResolvedValue(cart([rose, 1]));
    mocks.removeCart.mockResolvedValue(undefined);
    mocks.clearCart.mockResolvedValue(undefined);
    mocks.addWishlist.mockResolvedValue(undefined);
    mocks.removeWishlist.mockResolvedValue(undefined);
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
    localStorage.clear();
  });

  it("merges guest cart and favorites into an existing account without duplicates", async () => {
    mocks.merge.mockResolvedValue(merged(cart([rose, 5], [tulip, 1]), [rose, tulip]));
    const { result } = renderHook(useStore, { wrapper });
    await waitFor(() => expect(result.current.hydrated).toBe(true));
    act(() => {
      result.current.addToCart(roseProduct, 3);
      result.current.toggleFavorite(roseProduct);
      changeAuth(user(1));
    });
    await waitFor(() => expect(result.current.cartSyncBlocked).toBe(false));
    expect(mocks.merge).toHaveBeenCalledTimes(1);
    expect(mocks.merge.mock.calls[0][0]).toMatchObject({
      items: [{ product_slug: "rose", quantity: 3 }],
      wishlist: ["rose"],
    });
    expect(result.current.cart).toEqual({ rose: 5, tulip: 1 });
    expect(result.current.favorites).toEqual(["rose", "tulip"]);
    expect(mocks.addCart).not.toHaveBeenCalled();
    expect(localStorage.getItem("bloompetal:guest-merge:v1:1")).toBeNull();
  });

  it("merges into an empty account once despite StrictMode and auth refresh events", async () => {
    const { result } = renderHook(useStore, { wrapper });
    await waitFor(() => expect(result.current.hydrated).toBe(true));
    mocks.merge.mockResolvedValue(merged(cart([rose, 2]), [rose]));
    act(() => {
      result.current.addToCart(roseProduct, 2);
      result.current.toggleFavorite(roseProduct);
      changeAuth(user(1));
    });
    await waitFor(() => expect(result.current.cartSyncBlocked).toBe(false));
    act(() => changeAuth({ ...user(1), username: "new-name" }));
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 10));
    });
    expect(mocks.merge).toHaveBeenCalledTimes(1);
    expect(mocks.fetchCart).not.toHaveBeenCalled();
    expect(result.current.cart).toEqual({ rose: 2 });
    expect(result.current.name).toBe("new-name");
  });

  it("preserves the exact retry bundle after an ambiguous merge failure", async () => {
    mocks.merge
      .mockRejectedValueOnce(new Error("response lost"))
      .mockResolvedValueOnce(merged(cart([rose, 4]), [rose]));
    const { result } = renderHook(useStore, { wrapper });
    await waitFor(() => expect(result.current.hydrated).toBe(true));
    act(() => {
      result.current.addToCart(roseProduct, 2);
      result.current.toggleFavorite(roseProduct);
      changeAuth(user(1));
    });
    await waitFor(() => expect(result.current.cartError).toContain("Retry syncing"));
    const firstPayload = mocks.merge.mock.calls[0][0];
    expect(result.current.cart).toEqual({ rose: 2 });
    expect(result.current.cartSyncBlocked).toBe(true);
    expect(JSON.parse(localStorage.getItem("bloompetal:guest-merge:v1:1")!)[0].payload).toEqual(
      firstPayload,
    );
    await act(() => result.current.reloadCart());
    expect(mocks.merge.mock.calls[1][0]).toEqual(firstPayload);
    expect(result.current.cart).toEqual({ rose: 4 });
    expect(result.current.cartSyncBlocked).toBe(false);
  });

  it("recovers an unconfirmed merge after remount instead of submitting a new merge id", async () => {
    mocks.merge.mockRejectedValueOnce(new Error("offline"));
    const first = renderHook(useStore, { wrapper });
    await waitFor(() => expect(first.result.current.hydrated).toBe(true));
    act(() => {
      first.result.current.addToCart(roseProduct, 2);
      changeAuth(user(1));
    });
    await waitFor(() => expect(first.result.current.cartError).not.toBe(""));
    const firstPayload = mocks.merge.mock.calls[0][0];
    first.unmount();
    mocks.merge.mockResolvedValue(merged(cart([rose, 2])));
    const second = renderHook(useStore, { wrapper });
    await waitFor(() => expect(mocks.merge).toHaveBeenCalledTimes(2));
    await waitFor(() => expect(second.result.current.cartSyncBlocked).toBe(false));
    expect(mocks.merge.mock.calls[1][0]).toEqual(firstPayload);
    expect(second.result.current.cart).toEqual({ rose: 2 });
  });

  it("reuses the guest draft id if a tab closes before the account-owned snapshot was persisted", async () => {
    mocks.merge.mockRejectedValueOnce(new Error("offline"));
    const first = renderHook(useStore, { wrapper });
    await waitFor(() => expect(first.result.current.hydrated).toBe(true));
    act(() => first.result.current.addToCart(roseProduct, 2));
    const guestSnapshot = localStorage.getItem("bloompetal:v1")!;
    act(() => changeAuth(user(1)));
    await waitFor(() => expect(first.result.current.cartError).not.toBe(""));
    const firstPayload = mocks.merge.mock.calls[0][0];
    first.unmount();
    // Simulate interrupted persistence: the journal is durable, but the old
    // guest snapshot is still present. Its draft id must not become a new merge.
    localStorage.setItem("bloompetal:v1", guestSnapshot);
    mocks.merge.mockResolvedValue(merged(cart([rose, 2])));
    const second = renderHook(useStore, { wrapper });
    await waitFor(() => expect(second.result.current.cartSyncBlocked).toBe(false));
    expect(mocks.merge).toHaveBeenCalledTimes(2);
    expect(mocks.merge.mock.calls[1][0]).toEqual(firstPayload);
    expect(localStorage.getItem("bloompetal:guest-merge:v1:1")).toBeNull();
  });

  it("keeps another account's selections out of the guest cart and next merge", async () => {
    mocks.auth = { user: user(1), access: "a", refresh: "r" };
    mocks.fetchCart.mockResolvedValue(cart([rose, 2]));
    mocks.fetchWishlist.mockResolvedValue([rose]);
    const { result } = renderHook(useStore, { wrapper });
    await waitFor(() => expect(result.current.cart.rose).toBe(2));
    act(() => result.current.signOut());
    expect(result.current.cart).toEqual({});
    expect(result.current.favorites).toEqual([]);
    act(() => {
      result.current.addToCart(tulipProduct, 1);
      result.current.toggleFavorite(tulipProduct);
      changeAuth(user(2));
    });
    await waitFor(() => expect(mocks.merge).toHaveBeenCalledTimes(1));
    expect(mocks.merge.mock.calls[0][0]).toMatchObject({
      items: [{ product_slug: "tulip", quantity: 1 }],
      wishlist: ["tulip"],
    });
  });

  it("ignores an old account's delayed cart and wishlist load after logout", async () => {
    const cartLoad = deferred<ApiCart>();
    const wishlistLoad = deferred<ApiProductListItem[]>();
    mocks.auth = { user: user(1), access: "a", refresh: "r" };
    mocks.fetchCart.mockReturnValue(cartLoad.promise);
    mocks.fetchWishlist.mockReturnValue(wishlistLoad.promise);
    const { result } = renderHook(useStore, { wrapper });
    await waitFor(() => expect(mocks.fetchCart).toHaveBeenCalled());
    act(() => result.current.signOut());
    await act(async () => {
      cartLoad.resolve(cart([rose, 3]));
      wishlistLoad.resolve([rose]);
    });
    expect(result.current.user).toBeNull();
    expect(result.current.cart).toEqual({});
    expect(result.current.favorites).toEqual([]);
    expect(result.current.cartLoading).toBe(false);
  });

  it("ignores old mutation responses and drops queued writes when switching accounts", async () => {
    const firstAdd = deferred<ApiCart>();
    mocks.auth = { user: user(1), access: "a", refresh: "r" };
    const { result } = renderHook(useStore, { wrapper });
    await waitFor(() => expect(result.current.cartSyncBlocked).toBe(false));
    mocks.addCart.mockReturnValueOnce(firstAdd.promise);
    act(() => {
      result.current.addToCart(roseProduct, 1);
      result.current.addToCart(roseProduct, 1);
    });
    await waitFor(() => expect(mocks.addCart).toHaveBeenCalledTimes(1));
    mocks.fetchCart.mockResolvedValue(cart([tulip, 3]));
    act(() => changeAuth(user(2)));
    await waitFor(() => expect(result.current.cart.tulip).toBe(3));
    await act(async () => firstAdd.resolve(cart([rose, 1])));
    expect(mocks.addCart).toHaveBeenCalledTimes(1);
    expect(result.current.cart).toEqual({ tulip: 3 });
    expect(mocks.merge).not.toHaveBeenCalled();
  });

  it("serializes rapid cart changes without letting an older response overwrite the last edit", async () => {
    const firstAdd = deferred<ApiCart>();
    mocks.auth = { user: user(1), access: "a", refresh: "r" };
    const { result } = renderHook(useStore, { wrapper });
    await waitFor(() => expect(result.current.cartSyncBlocked).toBe(false));
    mocks.addCart.mockReturnValueOnce(firstAdd.promise).mockResolvedValueOnce(cart([rose, 2]));
    act(() => {
      result.current.addToCart(roseProduct, 1);
      result.current.addToCart(roseProduct, 1);
    });
    await waitFor(() => expect(mocks.addCart).toHaveBeenCalledTimes(1));
    expect(result.current.cart.rose).toBe(2);
    await act(async () => firstAdd.resolve(cart([rose, 1])));
    await waitFor(() => expect(mocks.addCart).toHaveBeenCalledTimes(2));
    expect(result.current.cart.rose).toBe(2);
  });

  it("keeps the retry bundle in memory when storage writes are blocked", async () => {
    const { result } = renderHook(useStore, { wrapper });
    await waitFor(() => expect(result.current.hydrated).toBe(true));
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("quota");
    });
    mocks.merge
      .mockRejectedValueOnce(new Error("offline"))
      .mockResolvedValueOnce(merged(cart([rose, 1])));
    act(() => {
      result.current.addToCart(roseProduct, 1);
      changeAuth(user(1));
    });
    await waitFor(() => expect(result.current.cartError).not.toBe(""));
    const firstPayload = mocks.merge.mock.calls[0][0];
    await act(() => result.current.reloadCart());
    expect(mocks.merge.mock.calls[1][0]).toEqual(firstPayload);
    expect(result.current.cart).toEqual({ rose: 1 });
  });

  it("clamps guest quantities to stock and never duplicates rapid favorite toggles", async () => {
    const { result } = renderHook(useStore, { wrapper });
    await waitFor(() => expect(result.current.hydrated).toBe(true));
    act(() => {
      result.current.addToCart(roseProduct, 10);
      result.current.toggleFavorite(roseProduct);
      result.current.toggleFavorite(roseProduct);
    });
    expect(result.current.cart).toEqual({ rose: 5 });
    expect(result.current.favorites).toEqual([]);
    act(() => result.current.setCartQty("rose", 500));
    expect(result.current.cart).toEqual({ rose: 5 });
    act(() => result.current.addToCart({ ...tulipProduct, stock: 0, isInStock: false }));
    expect(result.current.cart).toEqual({ rose: 5 });
  });

  it("does not re-merge a legacy signed-in snapshot on the first upgrade", async () => {
    mocks.auth = { user: user(1), access: "a", refresh: "r" };
    localStorage.setItem(
      "bloompetal:v1",
      JSON.stringify({
        cart: { rose: 2 },
        cartProducts: { rose: roseProduct },
        favorites: ["rose"],
      }),
    );
    const { result } = renderHook(useStore, { wrapper });
    await waitFor(() => expect(mocks.fetchCart).toHaveBeenCalled());
    await waitFor(() => expect(result.current.cartSyncBlocked).toBe(false));
    expect(mocks.merge).not.toHaveBeenCalled();
    expect(result.current.cart).toEqual({});
  });

  it("does not block a healthy cart solely because wishlist loading is unavailable", async () => {
    mocks.auth = { user: user(1), access: "a", refresh: "r" };
    localStorage.setItem(
      "bloompetal:v1",
      JSON.stringify({
        schemaVersion: 2,
        selectionOwner: 1,
        cart: {},
        favorites: ["tulip"],
        favoriteProducts: { tulip: tulipProduct },
      }),
    );
    mocks.fetchCart.mockResolvedValue(cart([rose, 1]));
    mocks.fetchWishlist.mockRejectedValue(new Error("temporarily unavailable"));
    const { result } = renderHook(useStore, { wrapper });
    await waitFor(() => expect(result.current.cart.rose).toBe(1));
    expect(result.current.cartSyncBlocked).toBe(false);
    expect(result.current.favorites).toEqual(["tulip"]);
    expect(result.current.cartError).toBe("");
  });
});
