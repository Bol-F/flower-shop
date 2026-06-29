"use client";

/* eslint-disable @next/next/no-img-element */
import Link from "next/link";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { formatPrice } from "@/lib/currency";
import {
  calculateDeliveryFee,
  deliveryTimeSlots,
  fallbackDeliveryZones,
  type DeliveryZoneOption,
  type DeliveryTimeSlot,
} from "@/lib/delivery";
import { copy, languages } from "@/lib/i18n";
import {
  ApiError,
  OfflineError,
  createOrder,
  fetchAdminSupportMessages,
  fetchCities,
  fetchDeliveryZones,
  payTestOrder,
  validatePromoCode,
  type ApiOrder,
  type ApiCity,
  type ApiPaymentMethod,
} from "@/lib/api";
import { useStore } from "@/lib/store";
import BouquetArt from "./BouquetArt";
import DeliveryMapPicker, { type DeliveryMapValue } from "./DeliveryMapPicker";
import {
  CartIcon,
  CloseIcon,
  MenuIcon,
  MinusIcon,
  PlusIcon,
  TrashIcon,
  UserIcon,
} from "./icons";

type DeliveryDayMode = "today" | "tomorrow" | "custom";

function formatDateInput(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function relativeDeliveryDate(mode: Exclude<DeliveryDayMode, "custom">): string {
  const date = new Date();
  if (mode === "tomorrow") {
    date.setDate(date.getDate() + 1);
  }
  return formatDateInput(date);
}

function cityToSlug(city: string) {
  return city
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

const paymentMethods: Array<{
  id: ApiPaymentMethod;
  label: string;
  detail: string;
}> = [
  { id: "cash", label: "Cash", detail: "Unpaid until delivery" },
  { id: "card", label: "Card", detail: "Pending staff confirmation" },
  { id: "online", label: "Online", detail: "Pending internal payment" },
];

function firstApiMessage(error: unknown, fallback: string) {
  if (error instanceof OfflineError) return fallback;
  if (error instanceof ApiError) {
    const first = Object.values(error.details)[0];
    if (Array.isArray(first) && typeof first[0] === "string") return first[0];
    if (typeof first === "string") return first;
    return error.message;
  }
  return error instanceof Error ? error.message : fallback;
}

function CartDropdown({ onClose }: { onClose: () => void }) {
  const {
    cartLines,
    currency,
    language,
    setCartQty,
    removeFromCart,
    user,
    city,
    clearCart,
    cartLoading,
    cartError,
    showToast,
  } = useStore();
  const t = copy[language].cart;
  const [checkoutOpen, setCheckoutOpen] = useState(false);
  const [deliveryLocation, setDeliveryLocation] = useState<DeliveryMapValue>({
    address: user?.address ?? "",
    lat: null,
    lng: null,
  });
  const [phone, setPhone] = useState(user?.phone ?? "");
  const [paymentMethod, setPaymentMethod] = useState<ApiPaymentMethod>("cash");
  const [promoCode, setPromoCode] = useState("");
  const [promoDiscount, setPromoDiscount] = useState(0);
  const [promoLoading, setPromoLoading] = useState(false);
  const [deliveryZones, setDeliveryZones] =
    useState<DeliveryZoneOption[]>(fallbackDeliveryZones);
  const [selectedDeliveryZoneId, setSelectedDeliveryZoneId] = useState(
    fallbackDeliveryZones[0].id,
  );
  const [deliveryDayMode, setDeliveryDayMode] =
    useState<DeliveryDayMode>("today");
  const [customDeliveryDate, setCustomDeliveryDate] = useState(
    relativeDeliveryDate("today"),
  );
  const [deliveryTimeSlot, setDeliveryTimeSlot] =
    useState<DeliveryTimeSlot>(deliveryTimeSlots[1]);
  const [recipientName, setRecipientName] = useState(user?.username ?? "");
  const [recipientPhone, setRecipientPhone] = useState(user?.phone ?? "");
  const [giftNote, setGiftNote] = useState("");
  const [callRecipientBeforeDelivery, setCallRecipientBeforeDelivery] =
    useState(true);
  const [notes, setNotes] = useState("");
  const [sendAsGift, setSendAsGift] = useState(false);
  const [showMapPicker, setShowMapPicker] = useState(false);
  const [showExtraDetails, setShowExtraDetails] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [createdOrder, setCreatedOrder] = useState<ApiOrder | null>(null);
  const [testPaying, setTestPaying] = useState(false);
  const [testPayError, setTestPayError] = useState("");
  const [error, setError] = useState("");
  const total = cartLines.reduce((sum, item) => sum + item.subtotal, 0);
  const selectedDeliveryZone =
    deliveryZones.find((zone) => zone.id === selectedDeliveryZoneId) ??
    deliveryZones[0] ??
    null;
  const deliveryFee = calculateDeliveryFee(total, selectedDeliveryZone);
  const finalTotal = Math.max(total + deliveryFee - promoDiscount, 0);
  const selectedDeliveryDate =
    deliveryDayMode === "custom"
      ? customDeliveryDate
      : relativeDeliveryDate(deliveryDayMode);
  const minDeliveryDate = relativeDeliveryDate("today");

  useEffect(() => {
    const isMobile = window.matchMedia("(max-width: 639px)").matches;
    if (!isMobile) return;

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, []);

  useEffect(() => {
    let active = true;

    async function loadDeliveryZones() {
      try {
        const zones = await fetchDeliveryZones(cityToSlug(city));
        if (!active || zones.length === 0) return;
        const mappedZones = zones.map((zone) => ({
          id: zone.id,
          name: zone.name,
          city: zone.city,
          fee: Number.parseFloat(zone.fee) || 0,
          requiresManualConfirmation: zone.requires_manual_confirmation,
          description: zone.description,
        }));
        setDeliveryZones(mappedZones);
        setSelectedDeliveryZoneId((current) =>
          mappedZones.some((zone) => zone.id === current)
            ? current
            : mappedZones[0].id,
        );
      } catch {
        if (active) setDeliveryZones(fallbackDeliveryZones);
      }
    }

    if (checkoutOpen) void loadDeliveryZones();

    return () => {
      active = false;
    };
  }, [checkoutOpen, city]);

  async function onApplyPromo() {
    const code = promoCode.trim();
    setError("");
    if (!code) {
      setPromoDiscount(0);
      return;
    }

    try {
      setPromoLoading(true);
      const result = await validatePromoCode({
        code,
        subtotal: total.toFixed(2),
      });
      setPromoCode(result.code);
      setPromoDiscount(Number.parseFloat(result.discount_amount) || 0);
    } catch (err) {
      setPromoDiscount(0);
      setError(err instanceof Error ? err.message : "Promo code is not valid.");
    } finally {
      setPromoLoading(false);
    }
  }

  async function onCheckout(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    if (!user) {
      setError("Sign in before checkout.");
      return;
    }
    if (!deliveryLocation.address.trim() || !phone.trim()) {
      setError("Delivery address and your phone are required.");
      return;
    }
    if (sendAsGift && (!recipientName.trim() || !recipientPhone.trim())) {
      setError("Recipient name and phone are required.");
      return;
    }
    if (!selectedDeliveryDate || !deliveryTimeSlot) {
      setError("Choose a delivery date and time slot.");
      return;
    }

    try {
      setSubmitting(true);
      const resolvedRecipientName = sendAsGift
        ? recipientName.trim()
        : user.username || "Recipient";
      const resolvedRecipientPhone = sendAsGift
        ? recipientPhone.trim()
        : phone.trim();
      const order = await createOrder({
        shipping_address: deliveryLocation.address.trim(),
        phone: phone.trim(),
        payment_method: paymentMethod,
        delivery_address: deliveryLocation.address.trim(),
        delivery_lat: deliveryLocation.lat,
        delivery_lng: deliveryLocation.lng,
        delivery_date: selectedDeliveryDate,
        delivery_time_slot: deliveryTimeSlot,
        delivery_zone_id:
          selectedDeliveryZone && selectedDeliveryZone.id > 0
            ? selectedDeliveryZone.id
            : null,
        city_slug: cityToSlug(city),
        promo_code: promoCode.trim(),
        recipient_name: resolvedRecipientName,
        recipient_phone: resolvedRecipientPhone,
        gift_note: giftNote.trim(),
        call_recipient_before_delivery:
          sendAsGift && callRecipientBeforeDelivery,
        notes: notes.trim(),
      });
      clearCart();
      setCreatedOrder(order);
      setTestPayError("");
      setCheckoutOpen(false);
      showToast(`Order #${order.id} created`);
      if (order.payment_method === "cash") onClose();
    } catch (err) {
      setError(firstApiMessage(err, "Could not create order."));
    } finally {
      setSubmitting(false);
    }
  }

  async function onPayTestOrder() {
    if (!createdOrder) return;
    setTestPayError("");
    try {
      setTestPaying(true);
      const updated = await payTestOrder(createdOrder.id);
      setCreatedOrder(updated);
      showToast(`Order #${updated.id} paid`);
    } catch (err) {
      setTestPayError(
        firstApiMessage(
          err,
          "Could not complete this test payment. Please try again.",
        ),
      );
    } finally {
      setTestPaying(false);
    }
  }

  const createdOrderNeedsTestPayment =
    createdOrder &&
    createdOrder.payment_provider === "test" &&
    (createdOrder.payment_method === "card" ||
      createdOrder.payment_method === "online") &&
    createdOrder.payment_status === "pending";

  return (
    <>
      <button
        type="button"
        aria-label="Close cart"
        onClick={onClose}
        className="fixed inset-0 top-[66px] z-[60] bg-ink/25 backdrop-blur-[2px] sm:hidden"
      />
      <div
        className={`fixed inset-x-3 bottom-3 top-[78px] z-[70] animate-fade-up overflow-y-auto rounded-[1.5rem] border border-line bg-card p-3 shadow-lift sm:absolute sm:inset-x-auto sm:bottom-auto sm:right-0 sm:top-[calc(100%+14px)] sm:z-50 sm:max-h-[calc(100vh-6rem)] sm:rounded-[1.75rem] sm:p-4 ${
          checkoutOpen
            ? showMapPicker
              ? "sm:w-[min(34rem,calc(100vw-2rem))]"
              : "sm:w-[min(28rem,calc(100vw-2rem))]"
            : "sm:w-[min(20rem,calc(100vw-2rem))]"
        }`}
      >
        <div className="flex items-center justify-between gap-3">
          <p className="font-display text-lg font-bold">{t.title}</p>
          <button
            type="button"
            aria-label="Close cart"
            onClick={onClose}
            className="grid size-9 place-items-center rounded-full bg-blush text-blossomdeep transition active:scale-95 sm:hidden"
          >
            <CloseIcon className="size-4.5" />
          </button>
        </div>

      {createdOrder ? (
        <div className="mt-4 rounded-2xl bg-paper p-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="font-display text-xl font-bold">
                Order #{createdOrder.id}
              </p>
              <p className="mt-1 text-sm font-semibold text-stone">
                {createdOrder.payment_method_display} ·{" "}
                {createdOrder.payment_status_display}
              </p>
            </div>
            <span
              className={`rounded-full px-3 py-1 text-xs font-extrabold ${
                createdOrder.payment_status === "paid"
                  ? "bg-mint text-leaf"
                  : "bg-[#fff3d8] text-[#9a6410]"
              }`}
            >
              {createdOrder.payment_status_display}
            </span>
          </div>

          {createdOrder.payment_reference && (
            <p className="mt-3 rounded-xl bg-white px-3 py-2 text-xs font-bold text-stone">
              Test ref {createdOrder.payment_reference}
            </p>
          )}

          {createdOrder.payment_method === "cash" ? (
            <p className="mt-3 text-sm font-semibold text-stone">
              Cash payment is due on delivery.
            </p>
          ) : createdOrder.payment_provider === "test" ? (
            <div className="mt-3 rounded-2xl border border-line bg-white p-3">
              <p className="text-sm font-bold text-ink">
                This is a test payment. No real money will be charged.
              </p>
              <p className="mt-1 text-xs font-semibold text-stone">
                No card details are needed or saved.
              </p>
              {createdOrderNeedsTestPayment ? (
                <button
                  type="button"
                  disabled={testPaying}
                  onClick={() => void onPayTestOrder()}
                  className="mt-3 w-full rounded-full bg-ink py-2.5 text-sm font-extrabold text-white transition hover:bg-raspberry disabled:cursor-wait disabled:opacity-70"
                >
                  {testPaying ? "Paying..." : "Pay test order"}
                </button>
              ) : createdOrder.payment_status === "paid" ? (
                <p className="mt-3 rounded-xl bg-mint px-3 py-2 text-sm font-bold text-leaf">
                  Test payment complete.
                </p>
              ) : (
                <p className="mt-3 rounded-xl bg-berrysoft px-3 py-2 text-sm font-bold text-berry">
                  Payment is {createdOrder.payment_status_display.toLowerCase()}.
                </p>
              )}
            </div>
          ) : (
            <p className="mt-3 rounded-2xl bg-berrysoft px-3 py-2 text-sm font-bold text-berry">
              Payment provider is not available in this demo checkout.
            </p>
          )}

          {testPayError && (
            <p className="mt-3 rounded-2xl bg-berrysoft px-3 py-2 text-xs font-bold text-berry">
              {testPayError}
            </p>
          )}

          <div className="mt-4 grid grid-cols-2 gap-2">
            <Link
              href="/profile"
              onClick={onClose}
              className="rounded-full border border-line py-2.5 text-center text-sm font-bold text-stone transition hover:border-blossomdeep hover:text-blossomdeep"
            >
              Order history
            </Link>
            <button
              type="button"
              onClick={onClose}
              className="rounded-full bg-blossomdeep py-2.5 text-sm font-extrabold text-white shadow-glow transition hover:bg-raspberry"
            >
              Done
            </button>
          </div>
        </div>
      ) : cartLines.length === 0 ? (
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
            <form onSubmit={onCheckout} className="mt-3 grid gap-3">
              <div>
                <div className="mb-1.5 flex items-center justify-between gap-3">
                  <label className="text-xs font-extrabold uppercase tracking-wider text-stone">
                    Delivery address
                  </label>
                  <button
                    type="button"
                    onClick={() => setShowMapPicker((open) => !open)}
                    className="text-xs font-extrabold text-blossomdeep transition hover:text-raspberry"
                  >
                    {showMapPicker ? "Use simple address" : "Choose on map"}
                  </button>
                </div>
                {showMapPicker ? (
                  <DeliveryMapPicker
                    value={deliveryLocation}
                    onChange={setDeliveryLocation}
                  />
                ) : (
                  <input
                    value={deliveryLocation.address}
                    onChange={(event) =>
                      setDeliveryLocation({
                        address: event.target.value,
                        lat: null,
                        lng: null,
                      })
                    }
                    placeholder="Street, building, apartment"
                    className="w-full min-w-0 rounded-2xl border border-line bg-paper px-3.5 py-2.5 text-sm outline-none transition placeholder:text-stone focus:border-blossomdeep"
                  />
                )}
              </div>

              <div>
                <label className="mb-1.5 block text-xs font-extrabold uppercase tracking-wider text-stone">
                  Contact phone
                </label>
                <input
                  value={phone}
                  onChange={(event) => setPhone(event.target.value)}
                  placeholder="+998 90 123 45 67"
                  className="w-full rounded-2xl border border-line bg-paper px-3.5 py-2.5 text-sm outline-none transition placeholder:text-stone focus:border-blossomdeep"
                />
              </div>

              <div className="grid gap-2 sm:grid-cols-2">
                <label className="block">
                  <span className="mb-1.5 block text-xs font-extrabold uppercase tracking-wider text-stone">
                    Day
                  </span>
                  <select
                    value={deliveryDayMode}
                    onChange={(event) =>
                      setDeliveryDayMode(event.target.value as DeliveryDayMode)
                    }
                    className="w-full rounded-2xl border border-line bg-paper px-3.5 py-2.5 text-sm font-bold outline-none transition focus:border-blossomdeep"
                  >
                    <option value="today">Today</option>
                    <option value="tomorrow">Tomorrow</option>
                    <option value="custom">Choose date</option>
                  </select>
                </label>
                <label className="block">
                  <span className="mb-1.5 block text-xs font-extrabold uppercase tracking-wider text-stone">
                    Zone
                  </span>
                  <select
                    value={selectedDeliveryZoneId}
                    onChange={(event) =>
                      setSelectedDeliveryZoneId(Number(event.target.value))
                    }
                    className="w-full rounded-2xl border border-line bg-paper px-3.5 py-2.5 text-sm font-bold outline-none transition focus:border-blossomdeep"
                  >
                    {deliveryZones.map((zone) => (
                      <option key={zone.id} value={zone.id}>
                        {zone.name}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="block">
                  <span className="mb-1.5 block text-xs font-extrabold uppercase tracking-wider text-stone">
                    Time
                  </span>
                  <select
                    value={deliveryTimeSlot}
                    onChange={(event) =>
                      setDeliveryTimeSlot(event.target.value as DeliveryTimeSlot)
                    }
                    className="w-full rounded-2xl border border-line bg-paper px-3.5 py-2.5 text-sm font-bold outline-none transition focus:border-blossomdeep"
                  >
                    {deliveryTimeSlots.map((slot) => (
                      <option key={slot} value={slot}>
                        {slot}
                      </option>
                    ))}
                  </select>
                </label>
                {selectedDeliveryZone?.requiresManualConfirmation && (
                  <p className="rounded-2xl bg-[#fff3d8] px-3 py-2 text-xs font-bold text-[#9a6410] sm:col-span-2">
                    Staff will confirm delivery availability and final fee for this zone.
                  </p>
                )}
                {deliveryDayMode === "custom" && (
                  <input
                    type="date"
                    min={minDeliveryDate}
                    value={customDeliveryDate}
                    onChange={(event) => setCustomDeliveryDate(event.target.value)}
                    className="w-full rounded-2xl border border-line bg-paper px-3.5 py-2.5 text-sm outline-none transition focus:border-blossomdeep sm:col-span-2"
                  />
                )}
              </div>

              <div className="grid gap-2 rounded-2xl bg-paper p-3">
                <label className="flex items-center gap-2 rounded-2xl bg-paper px-3.5 py-2.5 text-sm font-bold text-ink">
                  <input
                    type="checkbox"
                    checked={sendAsGift}
                    onChange={(event) => setSendAsGift(event.target.checked)}
                    className="size-4 accent-blossomdeep"
                  />
                  Send to someone else
                </label>

                {sendAsGift && (
                  <div className="grid gap-2">
                    <input
                      value={recipientName}
                      onChange={(event) => setRecipientName(event.target.value)}
                      placeholder="Recipient name"
                      className="w-full rounded-2xl border border-line bg-white px-3.5 py-2.5 text-sm outline-none transition placeholder:text-stone focus:border-blossomdeep"
                    />
                    <input
                      value={recipientPhone}
                      onChange={(event) => setRecipientPhone(event.target.value)}
                      placeholder="Recipient phone"
                      className="w-full rounded-2xl border border-line bg-white px-3.5 py-2.5 text-sm outline-none transition placeholder:text-stone focus:border-blossomdeep"
                    />
                    <textarea
                      value={giftNote}
                      onChange={(event) => setGiftNote(event.target.value)}
                      rows={2}
                      placeholder="Gift note"
                      className="w-full resize-none rounded-2xl border border-line bg-white px-3.5 py-2.5 text-sm outline-none transition placeholder:text-stone focus:border-blossomdeep"
                    />
                    <label className="flex items-center gap-2 px-1 text-sm font-bold text-ink">
                      <input
                        type="checkbox"
                        checked={callRecipientBeforeDelivery}
                        onChange={(event) =>
                          setCallRecipientBeforeDelivery(event.target.checked)
                        }
                        className="size-4 accent-blossomdeep"
                      />
                      Call recipient before delivery
                    </label>
                  </div>
                )}

                <button
                  type="button"
                  onClick={() => setShowExtraDetails((open) => !open)}
                  className="rounded-2xl border border-line bg-white px-3.5 py-2.5 text-left text-sm font-extrabold text-stone transition hover:border-blossomdeep hover:text-blossomdeep"
                >
                  {showExtraDetails ? "Hide courier note" : "Add courier note"}
                </button>
                {showExtraDetails && (
                  <textarea
                    value={notes}
                    onChange={(event) => setNotes(event.target.value)}
                    rows={2}
                    placeholder="Entrance, floor, landmark..."
                    className="w-full resize-none rounded-2xl border border-line bg-white px-3.5 py-2.5 text-sm outline-none transition placeholder:text-stone focus:border-blossomdeep"
                  />
                )}
              </div>

              <fieldset className="rounded-2xl bg-paper p-2">
                <legend className="px-1 text-xs font-extrabold uppercase tracking-wider text-stone">
                  Payment method
                </legend>
                <div className="mt-1 grid gap-2 sm:grid-cols-3">
                  {paymentMethods.map((method) => {
                    const active = paymentMethod === method.id;
                    return (
                      <button
                        key={method.id}
                        type="button"
                        aria-pressed={active}
                        onClick={() => setPaymentMethod(method.id)}
                        className={`min-h-20 rounded-xl px-3 py-2 text-left transition ${
                          active
                            ? "bg-blossomdeep text-white shadow-glow"
                            : "bg-white text-stone hover:text-ink"
                        }`}
                      >
                        <span className="block text-sm font-extrabold">
                          {method.label}
                        </span>
                        <span
                          className={`mt-1 block text-xs font-bold leading-snug ${
                            active ? "text-white/80" : "text-stone"
                          }`}
                        >
                          {method.detail}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </fieldset>

              <div className="flex gap-2 rounded-2xl bg-paper p-2">
                <input
                  value={promoCode}
                  onChange={(event) => {
                    setPromoCode(event.target.value);
                    setPromoDiscount(0);
                  }}
                  placeholder="Promo code"
                  className="min-w-0 flex-1 rounded-xl border border-line bg-white px-3 py-2 text-sm font-bold uppercase outline-none transition placeholder:normal-case placeholder:text-stone focus:border-blossomdeep"
                />
                <button
                  type="button"
                  disabled={promoLoading}
                  onClick={() => void onApplyPromo()}
                  className="rounded-xl bg-ink px-4 py-2 text-sm font-extrabold text-white transition hover:bg-raspberry disabled:cursor-wait disabled:opacity-70"
                >
                  {promoLoading ? "..." : "Apply"}
                </button>
              </div>

              <div className="rounded-2xl border border-line bg-paper p-3 text-sm">
                <div className="flex items-center justify-between gap-3">
                  <span className="text-stone">Flowers</span>
                  <span className="font-bold">{formatPrice(total, currency)}</span>
                </div>
                <div className="mt-1 flex items-center justify-between gap-3">
                  <span className="text-stone">
                    Delivery
                    {selectedDeliveryZone ? ` (${selectedDeliveryZone.name})` : ""}
                  </span>
                  <span className="font-bold">
                    {deliveryFee === 0 ? "Free" : formatPrice(deliveryFee, currency)}
                  </span>
                </div>
                {promoDiscount > 0 && (
                  <div className="mt-1 flex items-center justify-between gap-3">
                    <span className="text-stone">Promo</span>
                    <span className="font-bold text-leaf">
                      -{formatPrice(promoDiscount, currency)}
                    </span>
                  </div>
                )}
                <div className="mt-2 flex items-center justify-between gap-3 border-t border-line pt-2">
                  <span className="font-extrabold">Total</span>
                  <span className="font-display text-lg font-bold">
                    {formatPrice(finalTotal, currency)}
                  </span>
                </div>
              </div>

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
    </>
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

function CitySwitch() {
  const { city, setCity } = useStore();
  const [cities, setCities] = useState<ApiCity[]>([]);

  useEffect(() => {
    let active = true;
    async function loadCities() {
      try {
        const data = await fetchCities();
        if (active) setCities(data);
      } catch {
        if (active) setCities([]);
      }
    }
    void loadCities();
    return () => {
      active = false;
    };
  }, []);

  const options = cities.length
    ? cities.map((item) => item.name)
    : ["Tashkent", "Samarkand", "Bukhara"];

  return (
    <select
      value={city}
      onChange={(event) => setCity(event.target.value)}
      aria-label="Delivery city"
      className="rounded-full border border-line bg-blush px-3 py-2 text-sm font-extrabold text-blossomdeep outline-none transition focus:border-blossomdeep"
    >
      {options.map((item) => (
        <option key={item} value={item}>
          {item}
        </option>
      ))}
    </select>
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
    <header
      className={`sticky top-0 bg-white shadow-[0_1px_0_rgb(247_220_232)] ${
        cartOpen ? "z-[70]" : "z-40"
      }`}
    >
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
          <CitySwitch />
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
              <CitySwitch />
            </div>
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
