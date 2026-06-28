"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import {
  addCartItem,
  addWishlistItem,
  clearRemoteCart,
  fetchCart,
  fetchWishlist,
  loadAuth,
  logout as apiLogout,
  removeCartItem,
  removeWishlistItem,
  updateCartItem,
  type ApiCart,
  type AuthUser,
} from "./api";
import {
  apiProductToProduct,
  fallbackCatalogProducts,
} from "./catalog";
import type { CategoryId, Currency, Language, Product } from "./types";

/**
 * One small client store for everything that must survive navigation:
 * profile preferences (currency / name / city), favorites, the cart and
 * the catalog filters driven from the header. Persisted to localStorage.
 */

interface PersistedState {
  currency: Currency;
  language: Language;
  name: string;
  city: string;
  favorites: string[];
  cart: Record<string, number>;
  cartProducts: Record<string, Product>;
}

const DEFAULTS: PersistedState = {
  currency: "USD",
  language: "EN",
  name: "",
  city: "Tashkent",
  favorites: [],
  cart: {},
  cartProducts: {},
};

export interface CartLine {
  product: Product;
  qty: number;
  subtotal: number;
}

const STORAGE_KEY = "bloompetal:v1";

interface StoreValue extends PersistedState {
  hydrated: boolean;
  /* backend account (null when browsing as guest) */
  user: AuthUser | null;
  setUser: (u: AuthUser | null) => void;
  signOut: () => void;
  /* catalog filters (session-only) */
  query: string;
  category: CategoryId | null;
  setQuery: (q: string) => void;
  setCategory: (c: CategoryId | null) => void;
  /* preferences */
  setCurrency: (c: Currency) => void;
  setLanguage: (l: Language) => void;
  setName: (n: string) => void;
  setCity: (c: string) => void;
  /* favorites */
  toggleFavorite: (product: Product | string) => void;
  /* cart */
  addToCart: (product: Product | string, qty?: number) => void;
  setCartQty: (id: string, qty: number) => void;
  removeFromCart: (id: string) => void;
  clearCart: () => void;
  reloadCart: () => Promise<void>;
  cartLines: CartLine[];
  cartCount: number;
  cartLoading: boolean;
  cartError: string;
  /* feedback */
  showToast: (message: string) => void;
}

const StoreContext = createContext<StoreValue | null>(null);

const fallbackProductById = new Map(
  fallbackCatalogProducts.map((product) => [product.id, product]),
);

function hydratePersisted(raw: string | null): PersistedState {
  if (!raw) return DEFAULTS;
  const parsed = JSON.parse(raw) as Partial<PersistedState>;
  const cart = parsed.cart ?? {};
  const cartProducts = { ...(parsed.cartProducts ?? {}) };

  for (const id of Object.keys(cart)) {
    if (!cartProducts[id]) {
      const fallback = fallbackProductById.get(id);
      if (fallback) cartProducts[id] = fallback;
    }
  }

  return { ...DEFAULTS, ...parsed, cart, cartProducts };
}

function cartStateFromApi(cart: ApiCart): Pick<PersistedState, "cart" | "cartProducts"> {
  const quantities: Record<string, number> = {};
  const snapshots: Record<string, Product> = {};

  for (const item of cart.items) {
    const product = apiProductToProduct(item.product);
    quantities[product.id] = item.quantity;
    snapshots[product.id] = product;
  }

  return { cart: quantities, cartProducts: snapshots };
}

export function StoreProvider({ children }: { children: ReactNode }) {
  const [persisted, setPersisted] = useState<PersistedState>(DEFAULTS);
  const [user, setUserState] = useState<AuthUser | null>(null);
  const [hydrated, setHydrated] = useState(false);
  const [cartLoading, setCartLoading] = useState(false);
  const [cartError, setCartError] = useState("");
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState<CategoryId | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    // one-time hydration from localStorage: the server render must use
    // DEFAULTS, so the stored state can only be applied after mount
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      // eslint-disable-next-line react-hooks/set-state-in-effect
      if (raw) setPersisted(hydratePersisted(raw));
    } catch {
      /* corrupted storage — fall back to defaults */
    }
    const auth = loadAuth();
    if (auth?.user) {
      setUserState(auth.user);
      setPersisted((prev) => ({
        ...prev,
        name: auth.user.username || prev.name,
        city: auth.user.city || prev.city,
        currency: auth.user.currency || prev.currency,
        language: auth.user.language || prev.language,
      }));
    }
    setHydrated(true);
  }, []);

  const applyRemoteCart = useCallback((cart: ApiCart) => {
    setPersisted((prev) => ({ ...prev, ...cartStateFromApi(cart) }));
    setCartError("");
  }, []);

  const reloadCart = useCallback(async () => {
    if (!user) return;
    try {
      setCartLoading(true);
      applyRemoteCart(await fetchCart());
    } catch {
      setCartError("Could not sync cart with the server.");
    } finally {
      setCartLoading(false);
    }
  }, [applyRemoteCart, user]);

  const reloadWishlist = useCallback(async () => {
    if (!user) return;
    try {
      const products = await fetchWishlist();
      setPersisted((prev) => ({
        ...prev,
        favorites: products.map((product) => product.slug),
      }));
    } catch {
      /* local favorites remain usable if the wishlist API is unavailable */
    }
  }, [user]);

  useEffect(() => {
    if (!hydrated || !user) return;
    const timer = window.setTimeout(() => {
      void reloadCart();
      void reloadWishlist();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [hydrated, reloadCart, reloadWishlist, user]);

  useEffect(() => {
    if (!hydrated) return;
    localStorage.setItem(STORAGE_KEY, JSON.stringify(persisted));
  }, [persisted, hydrated]);

  const showToast = useCallback((message: string) => {
    setToast(message);
    if (toastTimer.current) clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => setToast(null), 2200);
  }, []);

  const signOut = useCallback(() => {
    apiLogout();
    setUserState(null);
    setPersisted((prev) => ({ ...prev, cart: {}, cartProducts: {} }));
  }, []);

  const setUser = useCallback((nextUser: AuthUser | null) => {
    setUserState(nextUser);
    if (!nextUser) return;
    setPersisted((prev) => ({
      ...prev,
      name: nextUser.username || prev.name,
      city: nextUser.city || prev.city,
      currency: nextUser.currency || prev.currency,
      language: nextUser.language || prev.language,
    }));
  }, []);

  const value = useMemo<StoreValue>(() => {
    const update = (patch: Partial<PersistedState>) =>
      setPersisted((prev) => ({ ...prev, ...patch }));

    const productFor = (productOrId: Product | string) => {
      if (typeof productOrId !== "string") return productOrId;
      return persisted.cartProducts[productOrId] ?? fallbackProductById.get(productOrId);
    };

    const updateLocalCart = (product: Product, qty: number, mode: "add" | "set") => {
      setPersisted((prev) => {
        const nextQty = mode === "add" ? (prev.cart[product.id] ?? 0) + qty : qty;
        const cart = { ...prev.cart };
        const cartProducts = { ...prev.cartProducts, [product.id]: product };
        if (nextQty <= 0) {
          delete cart[product.id];
          delete cartProducts[product.id];
        } else {
          cart[product.id] = nextQty;
        }
        return { ...prev, cart, cartProducts };
      });
    };

    const removeLocalCartItem = (id: string) => {
      setPersisted((prev) => {
        const cart = { ...prev.cart };
        const cartProducts = { ...prev.cartProducts };
        delete cart[id];
        delete cartProducts[id];
        return { ...prev, cart, cartProducts };
      });
    };

    const cartLines = Object.entries(persisted.cart).flatMap(([id, qty]) => {
      const product = persisted.cartProducts[id] ?? fallbackProductById.get(id);
      return product ? [{ product, qty, subtotal: product.price * qty }] : [];
    });

    return {
      ...persisted,
      hydrated,
      user,
      setUser,
      signOut,
      query,
      category,
      setQuery,
      setCategory,
      setCurrency: (currency) => update({ currency }),
      setLanguage: (language) => update({ language }),
      setName: (name) => update({ name }),
      setCity: (city) => update({ city }),
      toggleFavorite: (productOrId) => {
        const product = productFor(productOrId);
        const id = typeof productOrId === "string" ? productOrId : productOrId.id;
        const willRemove = persisted.favorites.includes(id);

        setPersisted((prev) => ({
          ...prev,
          favorites: willRemove
            ? prev.favorites.filter((f) => f !== id)
            : [...prev.favorites, id],
        }));

        if (user && product?.backendId) {
          const action = willRemove
            ? removeWishlistItem(product.backendId)
            : addWishlistItem(product.backendId);
          void action.catch(() => {
            showToast("Could not sync wishlist with the server.");
          });
        }
      },
      addToCart: (productOrId, qty = 1) => {
        const product = productFor(productOrId);
        if (!product) return;
        updateLocalCart(product, qty, "add");

        if (user && product.backendId) {
          void addCartItem(product.backendId, qty)
            .then(applyRemoteCart)
            .catch(() => {
              setCartError("Could not add item to the server cart.");
            });
        }
      },
      setCartQty: (id, qty) => {
        const product = productFor(id);
        if (!product) return;
        updateLocalCart(product, qty, "set");

        if (user && product.backendId) {
          const action =
            qty <= 0
              ? removeCartItem(product.backendId).then(() => undefined)
              : updateCartItem(product.backendId, qty).then(applyRemoteCart);
          void action.catch(() => {
            setCartError("Could not update the server cart.");
          });
        }
      },
      removeFromCart: (id) => {
        const product = productFor(id);
        removeLocalCartItem(id);
        if (user && product?.backendId) {
          void removeCartItem(product.backendId).catch(() => {
            setCartError("Could not remove item from the server cart.");
          });
        }
      },
      clearCart: () => {
        setPersisted((prev) => ({ ...prev, cart: {}, cartProducts: {} }));
        if (user) {
          void clearRemoteCart().catch(() => {
            setCartError("Could not clear the server cart.");
          });
        }
      },
      reloadCart,
      cartLines,
      cartCount: Object.values(persisted.cart).reduce((a, b) => a + b, 0),
      cartLoading,
      cartError,
      showToast,
    };
  }, [
    persisted,
    hydrated,
    user,
    setUser,
    signOut,
    query,
    category,
    applyRemoteCart,
    reloadCart,
    cartLoading,
    cartError,
    showToast,
  ]);

  return (
    <StoreContext.Provider value={value}>
      {children}
      {/* app-wide toast: one at a time, bottom center */}
      {toast && (
        <div
          role="status"
          className="fixed bottom-6 left-1/2 z-50 animate-fade-up"
          style={{ "--fade-up-x": "-50%" } as React.CSSProperties}
        >
          <div className="flex items-center gap-2.5 rounded-full bg-ink px-5 py-3 text-sm font-semibold text-paper shadow-lift">
            <span className="grid size-5 place-items-center rounded-full bg-blossom text-[11px] text-white">
              ✓
            </span>
            {toast}
          </div>
        </div>
      )}
    </StoreContext.Provider>
  );
}

export function useStore(): StoreValue {
  const ctx = useContext(StoreContext);
  if (!ctx) throw new Error("useStore must be used inside <StoreProvider>");
  return ctx;
}
