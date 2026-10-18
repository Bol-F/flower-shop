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
  fetchPaymentConfiguration,
  fetchWishlist,
  loadAuth,
  mergeGuestSelections,
  logout as apiLogout,
  removeCartItem,
  removeWishlistItem,
  subscribeAuth,
  updateCartItem,
  type ApiCart,
  type AuthUser,
} from "./api";
import { apiProductToProduct, fallbackCatalogProducts } from "./catalog";
import { formatPrice as formatCurrencyPrice, UZS_PER_USD } from "./currency";
import {
  emptySelection,
  hasSelections,
  newGuestMerge,
  pendingSelection,
  readPendingGuestMerges,
  selectionFrom,
  stockLimit,
  type PendingGuestMerge,
  type SelectionState,
} from "./selection-state";
import type { CategoryId, Currency, Language, Product } from "./types";

/**
 * One small client store for everything that must survive navigation:
 * profile preferences (currency / name / city), favorites, the cart and
 * the catalog filters driven from the header. Persisted to localStorage.
 */

interface PersistedState extends SelectionState {
  schemaVersion: 2;
  selectionOwner: number | null;
  guestSelectionId: string | null;
  currency: Currency;
  language: Language;
  name: string;
  city: string;
}

const DEFAULTS: PersistedState = {
  schemaVersion: 2,
  selectionOwner: null,
  guestSelectionId: null,
  currency: "USD",
  language: "EN",
  name: "",
  city: "Tashkent",
  ...emptySelection(),
};

export interface CartLine {
  product: Product;
  qty: number;
  subtotal: number;
}

const STORAGE_KEY = "bloompetal:v1";

interface StoreValue extends PersistedState {
  hydrated: boolean;
  paymentRate: number;
  syncPaymentRate: (rate: string) => void;
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
  clearCart: (options?: { remote?: boolean }) => void;
  reloadCart: () => Promise<void>;
  cartLines: CartLine[];
  cartCount: number;
  cartLoading: boolean;
  cartError: string;
  cartSyncBlocked: boolean;
  /* feedback */
  showToast: (message: string) => void;
}

const StoreContext = createContext<StoreValue | null>(null);

const fallbackProductById = new Map(
  fallbackCatalogProducts.map((product) => [product.id, product]),
);

function hydratePersisted(raw: string | null, currentUserId: number | null): PersistedState {
  if (!raw) return DEFAULTS;
  const parsed = JSON.parse(raw) as Partial<PersistedState>;
  const selections = selectionFrom(parsed);
  const { cart, cartProducts } = selections;

  for (const id of Object.keys(cart)) {
    if (!cartProducts[id]) {
      const fallback = fallbackProductById.get(id);
      if (fallback) cartProducts[id] = fallback;
    }
  }

  // v1 mixed guest and signed-in snapshots. If already signed in, treat that
  // legacy snapshot as account-owned rather than adding it a second time.
  const selectionOwner =
    parsed.schemaVersion === 2
      ? typeof parsed.selectionOwner === "number"
        ? parsed.selectionOwner
        : null
      : currentUserId;
  return {
    ...DEFAULTS,
    currency: parsed.currency === "UZS" ? "UZS" : "USD",
    language: parsed.language === "RU" || parsed.language === "UZ" ? parsed.language : "EN",
    name: typeof parsed.name === "string" ? parsed.name : "",
    city: typeof parsed.city === "string" ? parsed.city : "Tashkent",
    ...selections,
    selectionOwner,
    guestSelectionId:
      typeof parsed.guestSelectionId === "string" &&
      /^[0-9a-f-]{36}$/i.test(parsed.guestSelectionId)
        ? parsed.guestSelectionId
        : null,
  };
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
  const persistedRef = useRef(persisted);
  const [user, setUserState] = useState<AuthUser | null>(null);
  const [hydrated, setHydrated] = useState(false);
  const [paymentRate, setPaymentRate] = useState(UZS_PER_USD);
  const syncPaymentRate = useCallback((value: string) => {
    const rate = Number(value);
    if (Number.isFinite(rate) && rate > 0) setPaymentRate(rate);
  }, []);
  const [cartLoading, setCartLoading] = useState(false);
  const [cartError, setCartError] = useState("");
  const [cartSyncBlocked, setCartSyncBlocked] = useState(false);
  const blockedRef = useRef(false);
  const sessionRef = useRef({ userId: null as number | null, generation: 0 });
  const initializedRef = useRef(false);
  const pendingMemory = useRef(new Map<number, PendingGuestMerge[]>());
  const pendingStorageUnavailable = useRef(new Set<number>());
  const queueRef = useRef<Promise<unknown>>(Promise.resolve());
  const cartRevision = useRef(0);
  const wishlistRevision = useRef(0);
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState<CategoryId | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const commit = useCallback((change: (previous: PersistedState) => PersistedState) => {
    let next = change(persistedRef.current);
    if (next.selectionOwner === null && !next.guestSelectionId && hasSelections(next)) {
      next = { ...next, guestSelectionId: crypto.randomUUID() };
    }
    persistedRef.current = next;
    setPersisted(next);
  }, []);

  const blockCart = useCallback((blocked: boolean) => {
    blockedRef.current = blocked;
    setCartSyncBlocked(blocked);
  }, []);

  const readPending = useCallback((userId: number) => {
    if (pendingStorageUnavailable.current.has(userId)) {
      return pendingMemory.current.get(userId) ?? [];
    }
    try {
      const pending = readPendingGuestMerges(
        localStorage.getItem(`bloompetal:guest-merge:v1:${userId}`),
      );
      pendingMemory.current.set(userId, pending);
      return pending;
    } catch {
      pendingStorageUnavailable.current.add(userId);
      return pendingMemory.current.get(userId) ?? [];
    }
  }, []);

  const savePending = useCallback((userId: number, pending: PendingGuestMerge[]) => {
    pendingMemory.current.set(userId, pending);
    try {
      const key = `bloompetal:guest-merge:v1:${userId}`;
      if (pending.length) localStorage.setItem(key, JSON.stringify(pending));
      else localStorage.removeItem(key);
    } catch {
      // A blocked storage API still has the in-memory retry bundle for this tab.
      pendingStorageUnavailable.current.add(userId);
    }
  }, []);

  const showToast = useCallback((message: string) => {
    setToast(message);
    if (toastTimer.current) clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => setToast(null), 2200);
  }, []);

  const applyUser = useCallback(
    (nextUser: AuthUser | null) => {
      const nextId = nextUser?.id ?? null;
      const changed = sessionRef.current.userId !== nextId;
      if (changed) {
        sessionRef.current = { userId: nextId, generation: sessionRef.current.generation + 1 };
        queueRef.current = Promise.resolve();
        cartRevision.current += 1;
        wishlistRevision.current += 1;
        setCartLoading(false);
        setCartError("");
        blockCart(nextId !== null);
      }
      const previous = persistedRef.current;
      if (
        changed &&
        nextId !== null &&
        previous.selectionOwner === null &&
        hasSelections(previous)
      ) {
        const merge = newGuestMerge(previous, previous.guestSelectionId ?? crypto.randomUUID());
        if (merge) {
          const pending = readPending(nextId);
          if (!pending.some((item) => item.payload.merge_id === merge.payload.merge_id)) {
            savePending(nextId, [...pending, merge]);
          }
        }
      }
      commit((prev) => ({
        ...prev,
        ...(prev.selectionOwner === nextId
          ? {}
          : nextId === null
            ? emptySelection()
            : pendingSelection(readPending(nextId))),
        selectionOwner: nextId,
        guestSelectionId:
          nextId === null && prev.selectionOwner === null ? prev.guestSelectionId : null,
        name: nextUser?.username || (nextId === null ? "" : prev.name),
        city: nextUser?.city || prev.city,
        currency: nextUser?.currency || prev.currency,
        language: nextUser?.language || prev.language,
      }));
      setUserState(nextUser);
    },
    [blockCart, commit, readPending, savePending],
  );

  type Session = typeof sessionRef.current;
  const isCurrent = useCallback(
    (session: Session) =>
      session.userId !== null &&
      sessionRef.current.generation === session.generation &&
      sessionRef.current.userId === session.userId &&
      loadAuth()?.user.id === session.userId,
    [],
  );

  const enqueue = useCallback(
    (session: Session, action: () => Promise<void>) => {
      const task = queueRef.current.then(async () => {
        if (isCurrent(session)) await action();
      });
      // Keep a failed operation from preventing a later explicit retry.
      queueRef.current = task.catch(() => undefined);
      return task;
    },
    [isCurrent],
  );

  const applyRemoteCart = useCallback(
    (cart: ApiCart) => {
      commit((prev) => ({ ...prev, ...cartStateFromApi(cart) }));
      setCartError("");
    },
    [commit],
  );

  const reloadCart = useCallback(async () => {
    const session = sessionRef.current;
    if (session.userId === null) return;
    const expectedCartRevision = cartRevision.current;
    const expectedWishlistRevision = wishlistRevision.current;
    await enqueue(session, async () => {
      setCartLoading(true);
      try {
        let cart: ApiCart | undefined;
        let wishlist: Awaited<ReturnType<typeof fetchWishlist>> | undefined;
        for (const pending of readPending(session.userId!)) {
          if (!isCurrent(session)) return;
          const result = await mergeGuestSelections(pending.payload);
          if (!isCurrent(session)) return;
          // Only discard after confirmation. A lost response safely retries the
          // same merge id, never an additive POST for each guest cart item.
          savePending(
            session.userId!,
            readPending(session.userId!).filter(
              (item) => item.payload.merge_id !== pending.payload.merge_id,
            ),
          );
          cart = result.cart;
          wishlist = result.wishlist;
          if (result.adjusted_products.length || result.unavailable_products.length) {
            showToast("Your saved selections were updated to match current stock.");
          }
        }
        if (!cart || !wishlist) {
          const [remoteCart, remoteWishlist] = await Promise.allSettled([
            fetchCart(),
            fetchWishlist(),
          ]);
          if (remoteCart.status === "rejected") throw remoteCart.reason;
          cart = remoteCart.value;
          if (remoteWishlist.status === "fulfilled") wishlist = remoteWishlist.value;
          else if (isCurrent(session)) showToast("Could not sync wishlist with the server.");
        }
        if (!isCurrent(session)) return;
        if (cartRevision.current === expectedCartRevision) applyRemoteCart(cart);
        if (wishlist && wishlistRevision.current === expectedWishlistRevision) {
          const products = wishlist;
          commit((prev) => ({
            ...prev,
            favorites: products.map((product) => product.slug),
            favoriteProducts: Object.fromEntries(
              products.map((product) => [product.slug, apiProductToProduct(product)]),
            ),
          }));
        }
        blockCart(false);
        setCartError("");
      } catch {
        if (!isCurrent(session)) return;
        blockCart(true);
        setCartError("Your selections are saved. Retry syncing before checkout.");
      } finally {
        if (isCurrent(session)) setCartLoading(false);
      }
    });
  }, [applyRemoteCart, blockCart, commit, enqueue, isCurrent, readPending, savePending, showToast]);

  useEffect(() => {
    let active = true;
    void fetchPaymentConfiguration()
      .then((config) => {
        if (active) syncPaymentRate(config.uzs_per_price_unit);
      })
      .catch(() => {
        // Demo/offline catalog retains the documented default rate.
      });
    return () => {
      active = false;
    };
  }, [syncPaymentRate]);

  useEffect(() => {
    // one-time hydration from localStorage: the server render must use
    // DEFAULTS, so the stored state can only be applied after mount
    if (!initializedRef.current) {
      initializedRef.current = true;
      try {
        const state = hydratePersisted(
          localStorage.getItem(STORAGE_KEY),
          loadAuth()?.user.id ?? null,
        );
        commit(() => state);
      } catch {
        /* corrupted storage — fall back to defaults */
      }
    }
    const applyAuth = (auth: ReturnType<typeof loadAuth>) => {
      applyUser(auth?.user ?? null);
    };
    applyAuth(loadAuth());
    // Browser-only storage/auth hydration must follow the server's default render.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setHydrated(true);
    return subscribeAuth(applyAuth);
  }, [applyUser, commit]);

  const userId = user?.id ?? null;
  useEffect(() => {
    if (!hydrated || userId === null) return;
    const timer = window.setTimeout(() => {
      void reloadCart();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [hydrated, reloadCart, userId]);

  useEffect(() => {
    if (!hydrated) return;
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(persisted));
    } catch {
      // Keep checkout and sign-in usable when browser storage is unavailable.
    }
  }, [persisted, hydrated]);

  useEffect(() => {
    document.documentElement.lang = persisted.language.toLowerCase();
  }, [persisted.language]);

  const signOut = useCallback(() => {
    apiLogout();
    applyUser(null);
  }, [applyUser]);

  const setUser = applyUser;

  const setName = useCallback(
    (name: string) => {
      commit((prev) => (prev.name === name ? prev : { ...prev, name }));
    },
    [commit],
  );

  const syncCartMutation = useCallback(
    (action: () => Promise<ApiCart | void>) => {
      const session = sessionRef.current;
      const expectedRevision = cartRevision.current;
      void enqueue(session, async () => {
        try {
          const cart = await action();
          if (isCurrent(session) && cart && cartRevision.current === expectedRevision) {
            applyRemoteCart(cart);
          }
        } catch {
          if (!isCurrent(session)) return;
          blockCart(true);
          setCartError("Could not save your cart change. Retry syncing before checkout.");
        }
      });
    },
    [applyRemoteCart, blockCart, enqueue, isCurrent],
  );

  const value = useMemo<StoreValue>(() => {
    const update = (patch: Partial<PersistedState>) => commit((prev) => ({ ...prev, ...patch }));

    const productFor = (productOrId: Product | string) => {
      if (typeof productOrId !== "string") return productOrId;
      return (
        persistedRef.current.cartProducts[productOrId] ??
        persistedRef.current.favoriteProducts[productOrId] ??
        fallbackProductById.get(productOrId)
      );
    };

    const canEditSelections = () => {
      if (sessionRef.current.userId === null || !blockedRef.current) return true;
      showToast("Sync your saved selections before making more changes.");
      void reloadCart();
      return false;
    };

    const updateLocalCart = (product: Product, qty: number, mode: "add" | "set") => {
      cartRevision.current += 1;
      commit((prev) => {
        const requested = mode === "add" ? (prev.cart[product.id] ?? 0) + qty : qty;
        const nextQty = Math.min(Math.max(0, Math.floor(requested)), stockLimit(product));
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
      cartRevision.current += 1;
      commit((prev) => {
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
      paymentRate,
      syncPaymentRate,
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
      setName,
      setCity: (city) => update({ city }),
      toggleFavorite: (productOrId) => {
        if (!canEditSelections()) return;
        const product = productFor(productOrId);
        const id = typeof productOrId === "string" ? productOrId : productOrId.id;
        const willRemove = persistedRef.current.favorites.includes(id);
        if (!willRemove && persistedRef.current.favorites.length >= 100) {
          showToast("You can save up to 100 favorites.");
          return;
        }

        wishlistRevision.current += 1;
        commit((prev) => ({
          ...prev,
          favorites: willRemove ? prev.favorites.filter((f) => f !== id) : [...prev.favorites, id],
          favoriteProducts: product
            ? { ...prev.favoriteProducts, [id]: product }
            : prev.favoriteProducts,
        }));

        if (user && product?.backendId) {
          const session = sessionRef.current;
          void enqueue(session, async () => {
            try {
              if (willRemove) await removeWishlistItem(product.backendId!);
              else await addWishlistItem(product.backendId!);
            } catch {
              if (isCurrent(session)) showToast("Could not sync wishlist with the server.");
            }
          });
        }
      },
      addToCart: (productOrId, qty = 1) => {
        if (!canEditSelections() || !Number.isFinite(qty) || qty <= 0) return;
        const product = productFor(productOrId);
        if (!product) return;
        const previousQty = persistedRef.current.cart[product.id] ?? 0;
        if (previousQty === 0 && Object.keys(persistedRef.current.cart).length >= 100) {
          showToast("Your cart can contain up to 100 different products.");
          return;
        }
        updateLocalCart(product, qty, "add");
        const addedQty = (persistedRef.current.cart[product.id] ?? 0) - previousQty;

        if (user && product.backendId && addedQty > 0) {
          syncCartMutation(() => addCartItem(product.backendId!, addedQty));
        }
      },
      setCartQty: (id, qty) => {
        if (!canEditSelections() || !Number.isFinite(qty)) return;
        const product = productFor(id);
        if (!product) return;
        updateLocalCart(product, qty, "set");

        if (user && product.backendId) {
          const finalQty = persistedRef.current.cart[id] ?? 0;
          syncCartMutation(() =>
            finalQty <= 0
              ? removeCartItem(product.backendId!)
              : updateCartItem(product.backendId!, finalQty),
          );
        }
      },
      removeFromCart: (id) => {
        if (!canEditSelections()) return;
        const product = productFor(id);
        removeLocalCartItem(id);
        if (user && product?.backendId) {
          syncCartMutation(() => removeCartItem(product.backendId!));
        }
      },
      clearCart: (options) => {
        if (options?.remote !== false && !canEditSelections()) return;
        cartRevision.current += 1;
        commit((prev) => ({ ...prev, cart: {}, cartProducts: {} }));
        if (user && options?.remote !== false) {
          syncCartMutation(clearRemoteCart);
        }
      },
      reloadCart,
      cartLines,
      cartCount: Object.values(persisted.cart).reduce((a, b) => a + b, 0),
      cartLoading,
      cartError,
      cartSyncBlocked,
      showToast,
    };
  }, [
    persisted,
    paymentRate,
    syncPaymentRate,
    hydrated,
    user,
    setUser,
    setName,
    signOut,
    query,
    category,
    commit,
    enqueue,
    isCurrent,
    reloadCart,
    cartLoading,
    cartError,
    cartSyncBlocked,
    syncCartMutation,
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

export function usePriceFormatter(): (amount: number, currency: Currency) => string {
  const { paymentRate } = useStore();
  return useCallback(
    (amount: number, currency: Currency) => formatCurrencyPrice(amount, currency, paymentRate),
    [paymentRate],
  );
}
