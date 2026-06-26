"use client";

/* eslint-disable @next/next/no-img-element */
import Link from "next/link";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { formatPrice } from "@/lib/currency";
import { copy, languages } from "@/lib/i18n";
import { createOrder, fetchAdminSupportMessages } from "@/lib/api";
import { useStore } from "@/lib/store";
import BouquetArt from "./BouquetArt";
import {
  CartIcon,
  MenuIcon,
  MinusIcon,
  PlusIcon,
  TrashIcon,
  UserIcon,
} from "./icons";

function CartDropdown({ onClose }: { onClose: () => void }) {
  const {
    cartLines,
    currency,
    language,
    setCartQty,
    removeFromCart,
    user,
    clearCart,
    cartLoading,
    cartError,
    showToast,
  } = useStore();
  const t = copy[language].cart;
  const [checkoutOpen, setCheckoutOpen] = useState(false);
  const [shippingAddress, setShippingAddress] = useState(user?.address ?? "");
  const [phone, setPhone] = useState(user?.phone ?? "");
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const total = cartLines.reduce((sum, item) => sum + item.subtotal, 0);

  async function onCheckout(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    if (!user) {
      setError("Sign in before checkout.");
      return;
    }
    if (!shippingAddress.trim() || !phone.trim()) {
      setError("Delivery address and phone are required.");
      return;
    }

    try {
      setSubmitting(true);
      const order = await createOrder({
        shipping_address: shippingAddress.trim(),
        phone: phone.trim(),
        notes: notes.trim(),
      });
      clearCart();
      setCheckoutOpen(false);
      showToast(`Order #${order.id} created`);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create order.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="absolute right-0 top-[calc(100%+14px)] z-50 w-[min(20rem,calc(100vw-2rem))] animate-fade-up rounded-[1.75rem] border border-line bg-card p-4 shadow-lift">
      <p className="font-display text-lg font-bold">{t.title}</p>

      {cartLines.length === 0 ? (
        <div className="py-6 text-center">
          <p className="text-3xl">🌷</p>
          <p className="mt-2 text-sm text-stone">
            {cartLoading ? "Syncing cart..." : t.empty}
          </p>
        </div>
      ) : (
        <>
          <ul className="mt-3 flex max-h-72 flex-col gap-3 overflow-y-auto pr-1">
            {cartLines.map(({ product, qty }) => (
              <li key={product.id} className="flex items-center gap-3">
                <Link
                  href={`/product/${product.slug ?? product.id}`}
                  onClick={onClose}
                  className="grid size-14 shrink-0 place-items-center overflow-hidden rounded-2xl"
                  style={{ background: product.palette.backdrop }}
                >
                  {product.image ? (
                    <img
                      src={product.image}
                      alt={product.name}
                      className="h-full w-full object-cover"
                    />
                  ) : (
                    <BouquetArt palette={product.palette} className="h-12" />
                  )}
                </Link>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-semibold">{product.name}</p>
                  <p className="text-sm font-bold text-blossomdeep">
                    {formatPrice(product.price * qty, currency)}
                  </p>
                </div>
                <div className="flex items-center gap-1.5">
                  <button
                    type="button"
                    aria-label={`Decrease ${product.name} quantity`}
                    onClick={() => setCartQty(product.id, qty - 1)}
                    className="grid size-7 place-items-center rounded-full bg-blush text-raspberry transition hover:bg-blushdeep active:scale-90"
                  >
                    <MinusIcon className="size-3.5" />
                  </button>
                  <span className="w-5 text-center text-sm font-bold">{qty}</span>
                  <button
                    type="button"
                    aria-label={`Increase ${product.name} quantity`}
                    onClick={() => setCartQty(product.id, qty + 1)}
                    className="grid size-7 place-items-center rounded-full bg-blush text-raspberry transition hover:bg-blushdeep active:scale-90"
                  >
                    <PlusIcon className="size-3.5" />
                  </button>
                  <button
                    type="button"
                    aria-label={`Remove ${product.name} from cart`}
                    onClick={() => removeFromCart(product.id)}
                    className="ml-1 grid size-7 place-items-center rounded-full text-stone transition hover:bg-berrysoft hover:text-berry active:scale-90"
                  >
                    <TrashIcon className="size-3.5" />
                  </button>
                </div>
              </li>
            ))}
          </ul>

          <div className="mt-4 flex items-center justify-between border-t border-line pt-3">
            <span className="text-sm text-stone">{t.total}</span>
            <span className="font-display text-lg font-bold">
              {formatPrice(total, currency)}
            </span>
          </div>
          {(cartError || error) && (
            <p className="mt-3 rounded-2xl bg-berrysoft px-3 py-2 text-xs font-bold text-berry">
              {error || cartError}
            </p>
          )}

          {!checkoutOpen ? (
            user ? (
              <button
                type="button"
                onClick={() => setCheckoutOpen(true)}
                className="mt-3 w-full rounded-full bg-blossomdeep py-3 text-sm font-extrabold text-white shadow-glow transition hover:bg-raspberry active:scale-95"
              >
                {t.checkout}
              </button>
            ) : (
              <Link
                href="/profile?mode=login"
                onClick={onClose}
                className="mt-3 block w-full rounded-full bg-blossomdeep py-3 text-center text-sm font-extrabold text-white shadow-glow transition hover:bg-raspberry"
              >
                Sign in to checkout
              </Link>
            )
          ) : (
            <form onSubmit={onCheckout} className="mt-3 grid gap-2.5">
              <input
                value={shippingAddress}
                onChange={(event) => setShippingAddress(event.target.value)}
                placeholder="Delivery address"
                className="rounded-2xl border border-line bg-paper px-3.5 py-2.5 text-sm outline-none transition placeholder:text-stone focus:border-blossomdeep"
              />
              <input
                value={phone}
                onChange={(event) => setPhone(event.target.value)}
                placeholder="+998 90 123 45 67"
                className="rounded-2xl border border-line bg-paper px-3.5 py-2.5 text-sm outline-none transition placeholder:text-stone focus:border-blossomdeep"
              />
              <textarea
                value={notes}
                onChange={(event) => setNotes(event.target.value)}
                rows={2}
                placeholder="Delivery notes"
                className="resize-none rounded-2xl border border-line bg-paper px-3.5 py-2.5 text-sm outline-none transition placeholder:text-stone focus:border-blossomdeep"
              />
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setCheckoutOpen(false)}
                  className="rounded-full border border-line py-2.5 text-sm font-bold text-stone transition hover:border-blossomdeep hover:text-blossomdeep"
                >
                  Back
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="rounded-full bg-blossomdeep py-2.5 text-sm font-extrabold text-white shadow-glow transition hover:bg-raspberry disabled:cursor-wait disabled:opacity-70"
                >
                  {submitting ? "..." : "Place order"}
                </button>
              </div>
            </form>
          )}
        </>
      )}
    </div>
  );
}

function LanguageSwitch() {
  const { language, setLanguage } = useStore();

  return (
    <div className="flex items-center gap-1 rounded-full bg-blush px-2 py-1.5 text-sm font-extrabold text-blossomdeep">
      {languages.map((item) => {
        const active = language === item.id;
        return (
          <button
            key={item.id}
            type="button"
            aria-pressed={active}
            onClick={() => setLanguage(item.id)}
            className={`rounded-full px-3 py-1 transition active:scale-95 ${
              active ? "bg-blossomdeep text-white shadow-glow" : "hover:bg-white/70"
            }`}
          >
            {item.label}
          </button>
        );
      })}
    </div>
  );
}

export default function Header() {
  const { user, name, cartCount, hydrated, language, signOut } = useStore();
  const t = copy[language].nav;
  const [cartOpen, setCartOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [adminUnreadCount, setAdminUnreadCount] = useState(0);
  const cartRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!cartOpen) return;
    const onClick = (e: MouseEvent) => {
      if (cartRef.current && !cartRef.current.contains(e.target as Node)) {
        setCartOpen(false);
      }
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, [cartOpen]);

  const badgeCount = hydrated ? cartCount : 0;
  const displayName = user?.username || name || t.profile;
  const isSignedIn = hydrated && Boolean(user);
  const isStaff = Boolean(user?.is_staff);
  const visibleAdminUnreadCount = isStaff ? adminUnreadCount : 0;

  useEffect(() => {
    if (!hydrated || !isStaff) {
      return;
    }

    let active = true;
    async function loadUnread() {
      try {
        const data = await fetchAdminSupportMessages();
        if (!active) return;
        setAdminUnreadCount(
          data.filter((message) => !message.is_from_admin && !message.is_read)
            .length,
        );
      } catch {
        if (active) setAdminUnreadCount(0);
      }
    }

    void loadUnread();
    const timer = window.setInterval(() => {
      void loadUnread();
    }, 10000);

    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [hydrated, isStaff]);

  return (
    <header className="sticky top-0 z-40 bg-white shadow-[0_1px_0_rgb(247_220_232)]">
      <div className="mx-auto flex h-[66px] max-w-[1250px] items-center gap-5 px-5 sm:px-8 lg:px-0">
        <Link href="/" className="group flex shrink-0 items-center gap-3">
          <span className="text-2xl leading-none transition duration-300 group-hover:rotate-12 sm:text-3xl">
            🌸
          </span>
          <span className="font-display text-2xl font-extrabold tracking-normal text-blossomdeep sm:text-3xl">
            Bloom &amp; Petal
          </span>
        </Link>

        <nav className="ml-auto hidden items-center gap-8 text-base font-bold text-ink/80 lg:flex">
          {!isStaff && (
            <a href="#catalog" className="transition hover:text-blossomdeep">
              {t.shop}
            </a>
          )}
          {isSignedIn ? (
            <>
              {isStaff && (
                <Link
                  href="/admin"
                  className="relative inline-flex items-center gap-2 rounded-full bg-blush px-4 py-2 text-blossomdeep transition hover:bg-blushdeep"
                >
                  Messages
                  {visibleAdminUnreadCount > 0 && (
                    <span className="grid min-w-5 place-items-center rounded-full bg-blossomdeep px-1.5 text-[11px] font-extrabold leading-5 text-white">
                      {visibleAdminUnreadCount}
                    </span>
                  )}
                </Link>
              )}
              <Link
                href="/profile"
                className="flex items-center gap-2 rounded-full bg-blush px-2.5 py-1.5 pr-4 text-blossomdeep transition hover:bg-blushdeep"
              >
                <span className="grid size-8 place-items-center rounded-full bg-blossomdeep text-sm font-extrabold text-white shadow-glow">
                  {displayName.trim().charAt(0).toUpperCase() || (
                    <UserIcon className="size-4" />
                  )}
                </span>
                <span className="max-w-32 truncate">{displayName}</span>
              </Link>
              <button
                type="button"
                onClick={signOut}
                className="rounded-full border border-line px-4 py-2 text-sm font-extrabold text-stone transition hover:border-blossomdeep hover:text-blossomdeep"
              >
                Sign out
              </button>
            </>
          ) : hydrated ? (
            <>
              <Link href="/profile?mode=login" className="transition hover:text-blossomdeep">
                {t.login}
              </Link>
              <Link
                href="/profile"
                className="rounded-full bg-blossomdeep px-4 py-2 text-base font-extrabold text-white shadow-glow transition hover:-translate-y-0.5 hover:bg-raspberry active:translate-y-0"
              >
                {t.signUp}
              </Link>
            </>
          ) : null}
          <LanguageSwitch />
        </nav>

        <div className="ml-auto flex items-center gap-1.5 lg:ml-0">
          {!isStaff && (
            <div ref={cartRef} className="relative">
              <button
                type="button"
                aria-label={`Cart (${badgeCount} items)`}
                aria-expanded={cartOpen}
                onClick={() => setCartOpen(!cartOpen)}
                className={`relative grid size-10 place-items-center rounded-full text-ink/65 transition hover:bg-blush hover:text-blossomdeep ${
                  cartOpen ? "bg-blush text-blossomdeep" : ""
                }`}
              >
                <CartIcon className="size-5.5" />
                {badgeCount > 0 && (
                  <span
                    key={badgeCount}
                    className="absolute right-0 top-0 grid min-w-5 animate-pop place-items-center rounded-full bg-blossomdeep px-1 text-[10px] font-bold text-white"
                  >
                    {badgeCount}
                  </span>
                )}
              </button>
              {cartOpen && <CartDropdown onClose={() => setCartOpen(false)} />}
            </div>
          )}

          <button
            type="button"
            aria-label="Open menu"
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen(!menuOpen)}
            className="grid size-12 place-items-center rounded-full text-blossomdeep transition hover:bg-blush lg:hidden"
          >
            <MenuIcon className="size-6" />
          </button>
        </div>
      </div>

      {menuOpen && (
        <div className="border-t border-line bg-white px-5 py-4 shadow-soft lg:hidden">
          <nav className="mx-auto flex max-w-[1480px] flex-col gap-3 text-base font-bold">
            {!isStaff && (
              <a
                href="#catalog"
                onClick={() => setMenuOpen(false)}
                className="rounded-2xl px-3 py-2 transition hover:bg-blush"
              >
                {t.shop}
              </a>
            )}
            <Link
              href={isSignedIn ? "/profile" : "/profile?mode=login"}
              onClick={() => setMenuOpen(false)}
              className="flex items-center gap-2 rounded-2xl px-3 py-2 transition hover:bg-blush"
            >
              {isSignedIn && (
                <span className="grid size-8 place-items-center rounded-full bg-blossomdeep text-xs font-extrabold text-white">
                  {displayName.trim().charAt(0).toUpperCase()}
                </span>
              )}
              {isSignedIn ? displayName : t.login}
            </Link>
            {!isSignedIn && hydrated && (
              <Link
                href="/profile"
                onClick={() => setMenuOpen(false)}
                className="rounded-full bg-blossomdeep px-5 py-3 text-center font-extrabold text-white"
              >
                {t.signUp}
              </Link>
            )}
            {isSignedIn && isStaff && (
              <Link
                href="/admin"
                onClick={() => setMenuOpen(false)}
                className="flex items-center justify-between rounded-2xl px-3 py-2 transition hover:bg-blush"
              >
                <span>Messages</span>
                {visibleAdminUnreadCount > 0 && (
                  <span className="grid min-w-6 place-items-center rounded-full bg-blossomdeep px-2 text-xs font-extrabold leading-6 text-white">
                    {visibleAdminUnreadCount}
                  </span>
                )}
              </Link>
            )}
            {isSignedIn && (
              <button
                type="button"
                onClick={() => {
                  signOut();
                  setMenuOpen(false);
                }}
                className="rounded-full border border-line px-5 py-3 text-left font-extrabold text-stone transition hover:border-blossomdeep hover:text-blossomdeep"
              >
                Sign out
              </button>
            )}
            <div className="pt-1">
              <LanguageSwitch />
            </div>
            {isSignedIn && !isStaff && (
              <Link
                href="/profile#favorites"
                onClick={() => setMenuOpen(false)}
                className="flex items-center gap-2 rounded-2xl px-3 py-2 transition hover:bg-blush sm:hidden"
              >
                <UserIcon className="size-5" />
                {t.favorites}
              </Link>
            )}
          </nav>
        </div>
      )}
    </header>
  );
}
