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
import type { CategoryId, Currency, Language } from "./types";
import { loadAuth, logout as apiLogout, type AuthUser } from "./api";

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
}

const DEFAULTS: PersistedState = {
  currency: "USD",
  language: "EN",
  name: "",
  city: "Tashkent",
  favorites: [],
  cart: {},
};

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
  toggleFavorite: (id: string) => void;
  /* cart */
  addToCart: (id: string, qty?: number) => void;
  setCartQty: (id: string, qty: number) => void;
  removeFromCart: (id: string) => void;
  cartCount: number;
  /* feedback */
  showToast: (message: string) => void;
}

const StoreContext = createContext<StoreValue | null>(null);

export function StoreProvider({ children }: { children: ReactNode }) {
  const [persisted, setPersisted] = useState<PersistedState>(DEFAULTS);
  const [user, setUserState] = useState<AuthUser | null>(null);
  const [hydrated, setHydrated] = useState(false);
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
      if (raw) setPersisted({ ...DEFAULTS, ...JSON.parse(raw) });
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
      toggleFavorite: (id) =>
        setPersisted((prev) => ({
          ...prev,
          favorites: prev.favorites.includes(id)
            ? prev.favorites.filter((f) => f !== id)
            : [...prev.favorites, id],
        })),
      addToCart: (id, qty = 1) =>
        setPersisted((prev) => ({
          ...prev,
          cart: { ...prev.cart, [id]: (prev.cart[id] ?? 0) + qty },
        })),
      setCartQty: (id, qty) =>
        setPersisted((prev) => {
          const cart = { ...prev.cart };
          if (qty <= 0) delete cart[id];
          else cart[id] = qty;
          return { ...prev, cart };
        }),
      removeFromCart: (id) =>
        setPersisted((prev) => {
          const cart = { ...prev.cart };
          delete cart[id];
          return { ...prev, cart };
        }),
      cartCount: Object.values(persisted.cart).reduce((a, b) => a + b, 0),
      showToast,
    };
  }, [persisted, hydrated, user, setUser, signOut, query, category, showToast]);

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
