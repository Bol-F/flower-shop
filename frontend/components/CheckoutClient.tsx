"use client";

/* eslint-disable @next/next/no-img-element */
import Link from "next/link";
import { useEffect, useRef, useState, type FormEvent } from "react";
import {
  ApiError,
  OfflineError,
  createOrder,
  fetchCities,
  fetchDeliveryZones,
  fetchPaymentConfiguration,
  initializePayment,
  payTestOrder,
  validatePromoCode,
  type ApiCity,
  type ApiDeliveryZone,
  type ApiOrder,
  type ApiPaymentAttempt,
  type ApiPaymentOption,
} from "@/lib/api";
import { calculateDeliveryFee, deliveryTimeSlots } from "@/lib/delivery";
import { copy } from "@/lib/i18n";
import { usePriceFormatter, useStore } from "@/lib/store";
import BouquetArt from "./BouquetArt";
import DeliveryMapPicker, { type DeliveryMapValue } from "./DeliveryMapPicker";
import { ArrowRightIcon, MinusIcon, PlusIcon, TrashIcon } from "./icons";

const cashOption: ApiPaymentOption = {
  id: "cash",
  payment_method: "cash",
  provider: "cash",
  label: "Cash on delivery",
  detail: "Pay the courier when your flowers arrive",
  enabled: true,
  test_mode: false,
};
const activePaymentStatuses = new Set(["created", "pending", "processing"]);

type ZoneState = {
  city: string;
  status: "loading" | "ready" | "empty" | "error";
  zones: ApiDeliveryZone[];
};

function cityToSlug(city: string) {
  return city
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function dateInputValue(date = new Date()) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

function apiMessage(error: unknown, fallback: string) {
  if (error instanceof OfflineError) return fallback;
  if (error instanceof ApiError) {
    const first = Object.values(error.details)[0];
    if (Array.isArray(first) && typeof first[0] === "string") return first[0];
    if (typeof first === "string") return first;
  }
  return error instanceof Error ? error.message : fallback;
}

export default function CheckoutClient() {
  const { hydrated, user } = useStore();
  if (!hydrated) {
    return (
      <main className="site-container checkout-page" aria-busy="true">
        <h1 className="checkout-title">Your bag</h1>
        <p role="status">Loading your saved selections…</p>
      </main>
    );
  }
  // Mount after hydration for correct profile defaults; reset private form/result
  // state when the account changes, without resetting it on token refresh.
  return <CheckoutFlow key={user?.id ?? "guest"} />;
}

function CheckoutFlow() {
  const {
    cartLines,
    currency,
    language,
    user,
    city,
    setCity,
    setCartQty,
    removeFromCart,
    clearCart,
    cartLoading,
    cartSyncBlocked,
    cartError,
    reloadCart,
    showToast,
    syncPaymentRate,
  } = useStore();
  const formatPrice = usePriceFormatter();
  const t = copy[language].cart;
  const mounted = useRef(true);
  const submittingLock = useRef(false);
  const [checkoutOpen, setCheckoutOpen] = useState(false);
  const [deliveryLocation, setDeliveryLocation] = useState<DeliveryMapValue>({
    address: user?.address ?? "",
    lat: null,
    lng: null,
  });
  const [phone, setPhone] = useState(user?.phone ?? "");
  const [deliveryDate, setDeliveryDate] = useState(() => dateInputValue());
  const [timeSlot, setTimeSlot] = useState<string>(deliveryTimeSlots[1]);
  const [sendAsGift, setSendAsGift] = useState(false);
  const [recipientName, setRecipientName] = useState(user?.username ?? "");
  const [recipientPhone, setRecipientPhone] = useState(user?.phone ?? "");
  const [giftNote, setGiftNote] = useState("");
  const [callRecipient, setCallRecipient] = useState(true);
  const [notes, setNotes] = useState("");
  const [showMap, setShowMap] = useState(false);
  const [cities, setCities] = useState<ApiCity[]>([]);
  const [cityAttempt, setCityAttempt] = useState(0);
  const [citiesError, setCitiesError] = useState(false);
  const citySlug = cityToSlug(city);
  const [zoneState, setZoneState] = useState<ZoneState>({
    city: citySlug,
    status: "loading",
    zones: [],
  });
  const [selectedZoneId, setSelectedZoneId] = useState<number | null>(null);
  const [zoneAttempt, setZoneAttempt] = useState(0);
  const [paymentOptions, setPaymentOptions] = useState<ApiPaymentOption[]>([cashOption]);
  const [paymentOptionId, setPaymentOptionId] = useState<ApiPaymentOption["id"]>("cash");
  const [paymentLoading, setPaymentLoading] = useState(true);
  const [paymentError, setPaymentError] = useState("");
  const [promoCode, setPromoCode] = useState("");
  const [promo, setPromo] = useState<{ code: string; subtotal: number; discount: number } | null>(
    null,
  );
  const [promoLoading, setPromoLoading] = useState(false);
  const [promoError, setPromoError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [createdOrder, setCreatedOrder] = useState<ApiOrder | null>(null);
  const [createdPayment, setCreatedPayment] = useState<ApiPaymentAttempt | null>(null);
  const [paymentPreparing, setPaymentPreparing] = useState(false);
  const [testPaying, setTestPaying] = useState(false);
  const [paymentActionError, setPaymentActionError] = useState("");
  const subtotal = cartLines.reduce((sum, line) => sum + line.subtotal, 0);
  const vendors = new Set(
    cartLines.flatMap(({ product }) => (product.vendor ? [product.vendor] : [])),
  );
  const mixedFlorists = vendors.size > 1;
  const zonesCurrent = zoneState.city === citySlug;
  const zoneStatus = zonesCurrent ? zoneState.status : "loading";
  const selectedZone =
    zonesCurrent && zoneState.status === "ready"
      ? (zoneState.zones.find((zone) => zone.id === selectedZoneId) ?? null)
      : null;
  const selectedPayment = paymentOptions.find(
    (option) => option.id === paymentOptionId && option.enabled,
  );
  const deliveryFee = selectedZone
    ? calculateDeliveryFee(subtotal, {
        fee: Number(selectedZone.fee),
        freeDeliveryThreshold:
          selectedZone.free_delivery_threshold === undefined
            ? undefined
            : Number(selectedZone.free_delivery_threshold),
      })
    : null;
  const promoDiscount =
    promo?.code === promoCode.trim() && promo.subtotal === subtotal ? promo.discount : 0;
  const promoNeedsRefresh =
    Boolean(promoCode.trim()) &&
    (!promo || promo.code !== promoCode.trim() || promo.subtotal !== subtotal);
  const total = Math.max(subtotal + (deliveryFee ?? 0) - promoDiscount, 0);
  const cartBlocked = cartLoading || cartSyncBlocked;
  const canSubmit =
    !cartBlocked &&
    !mixedFlorists &&
    Boolean(selectedZone && selectedPayment) &&
    !paymentLoading &&
    !promoNeedsRefresh &&
    !submitting;

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  useEffect(() => {
    let active = true;
    void fetchCities()
      .then((items) => {
        if (active) {
          setCities(items.filter((item) => item.is_active));
          setCitiesError(false);
        }
      })
      .catch(() => {
        if (active) setCitiesError(true);
      });
    return () => {
      active = false;
    };
  }, [cityAttempt]);

  useEffect(() => {
    let active = true;
    // A response is tagged with its city, so even the render before this effect
    // cannot reuse a previously selected city's delivery zone.
    void fetchDeliveryZones(citySlug)
      .then((items) => {
        if (!active) return;
        const zones = items.filter(
          (zone) =>
            zone.id > 0 &&
            zone.is_active &&
            zone.city_slug === citySlug &&
            Number.isFinite(Number(zone.fee)) &&
            Number(zone.fee) >= 0,
        );
        setZoneState({ city: citySlug, status: zones.length ? "ready" : "empty", zones });
        setSelectedZoneId(zones[0]?.id ?? null);
      })
      .catch(() => {
        if (active) {
          setZoneState({ city: citySlug, status: "error", zones: [] });
          setSelectedZoneId(null);
        }
      });
    return () => {
      active = false;
    };
  }, [citySlug, zoneAttempt]);

  useEffect(() => {
    let active = true;
    void fetchPaymentConfiguration()
      .then((configuration) => {
        if (!active) return;
        syncPaymentRate(configuration.uzs_per_price_unit);
        const enabled = configuration.methods.filter((option) => option.enabled);
        setPaymentOptions(enabled.length ? enabled : [cashOption]);
        setPaymentOptionId((current) =>
          enabled.some((option) => option.id === current) ? current : (enabled[0]?.id ?? "cash"),
        );
      })
      .catch(() => {
        if (active) {
          setPaymentOptions([cashOption]);
          setPaymentOptionId("cash");
          setPaymentError(
            "Card payment is temporarily unavailable. Cash on delivery is still available.",
          );
        }
      })
      .finally(() => {
        if (active) setPaymentLoading(false);
      });
    return () => {
      active = false;
    };
  }, [syncPaymentRate]);

  function changeCity(nextCity: string) {
    setZoneState({ city: cityToSlug(nextCity), status: "loading", zones: [] });
    setSelectedZoneId(null);
    setCity(nextCity);
  }

  function retryZones() {
    setZoneState({ city: citySlug, status: "loading", zones: [] });
    setSelectedZoneId(null);
    setZoneAttempt((attempt) => attempt + 1);
  }

  async function applyPromo() {
    const code = promoCode.trim();
    setPromoError("");
    if (!code) {
      setPromo(null);
      return;
    }
    try {
      setPromoLoading(true);
      const result = await validatePromoCode({ code, subtotal: subtotal.toFixed(2) });
      if (!mounted.current) return;
      setPromoCode(result.code);
      setPromo({ code: result.code, subtotal, discount: Number(result.discount_amount) || 0 });
    } catch (reason) {
      if (mounted.current) {
        setPromo(null);
        setPromoError(apiMessage(reason, "Could not apply this promo code."));
      }
    } finally {
      if (mounted.current) setPromoLoading(false);
    }
  }

  async function preparePayment(order: ApiOrder, retry = false) {
    if (order.payment_method === "cash") return;
    const current = order.latest_payment;
    if (current && activePaymentStatuses.has(current.status)) {
      setCreatedPayment(current);
      return;
    }
    const provider = current?.provider ?? order.payment_provider;
    if (provider !== "test" && provider !== "payme" && provider !== "click") {
      setPaymentActionError("Payment is not available for this order. View your orders for help.");
      return;
    }
    setPaymentActionError("");
    setPaymentPreparing(true);
    try {
      const payment = await initializePayment(
        order.id,
        provider,
        retry ? `retry-${order.id}-${crypto.randomUUID()}` : `checkout-${order.id}-${provider}`,
      );
      if (!mounted.current) return;
      setCreatedPayment(payment);
      setCreatedOrder((previous) =>
        previous?.id === order.id ? { ...previous, latest_payment: payment } : previous,
      );
    } catch (reason) {
      if (mounted.current)
        setPaymentActionError(
          apiMessage(reason, "Could not prepare payment. Your order is saved; please retry."),
        );
    } finally {
      if (mounted.current) setPaymentPreparing(false);
    }
  }

  async function submitOrder(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (submittingLock.current) return;
    setError("");
    if (!user) {
      setError("Sign in before checkout.");
      return;
    }
    if (cartBlocked) {
      setError("Sync your cart before checkout so the order matches your selection.");
      return;
    }
    if (mixedFlorists) {
      setError("Items from different florists must be checked out separately.");
      return;
    }
    if (!selectedZone) {
      setError("Choose an available delivery zone for your city.");
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
    if (
      !deliveryDate ||
      deliveryDate < dateInputValue() ||
      !deliveryTimeSlots.some((slot) => slot === timeSlot)
    ) {
      setError("Choose a valid delivery date and time slot.");
      return;
    }
    if (!selectedPayment || paymentLoading) {
      setError("Choose an available payment method.");
      return;
    }
    if (promoNeedsRefresh) {
      setPromoError("Apply your promo code before placing the order, or clear the code.");
      return;
    }
    submittingLock.current = true;
    setSubmitting(true);
    try {
      const order = await createOrder({
        shipping_address: deliveryLocation.address.trim(),
        phone: phone.trim(),
        payment_method: selectedPayment.payment_method,
        delivery_address: deliveryLocation.address.trim(),
        delivery_lat: deliveryLocation.lat,
        delivery_lng: deliveryLocation.lng,
        delivery_date: deliveryDate,
        delivery_time_slot: timeSlot,
        delivery_zone_id: selectedZone.id,
        city_slug: citySlug,
        promo_code: promoCode.trim(),
        recipient_name: sendAsGift ? recipientName.trim() : user.username || "Recipient",
        recipient_phone: sendAsGift ? recipientPhone.trim() : phone.trim(),
        gift_note: giftNote.trim(),
        call_recipient_before_delivery: sendAsGift && callRecipient,
        notes: notes.trim(),
      });
      if (!mounted.current) return;
      setCreatedOrder(order);
      setCreatedPayment(order.latest_payment);
      // The server clears its cart within atomic order creation. A remote DELETE
      // here could erase selections added from a different tab afterwards.
      clearCart({ remote: false });
      showToast(`Order #${order.id} created`);
      if (order.payment_method !== "cash") await preparePayment(order);
    } catch (reason) {
      if (mounted.current)
        setError(apiMessage(reason, "Could not place your order. Please try again."));
    } finally {
      submittingLock.current = false;
      if (mounted.current) setSubmitting(false);
    }
  }

  async function completeTestPayment() {
    if (!createdOrder || testPaying) return;
    setPaymentActionError("");
    setTestPaying(true);
    try {
      const order = await payTestOrder(createdOrder.id);
      if (!mounted.current) return;
      setCreatedOrder(order);
      setCreatedPayment(order.latest_payment);
      showToast(`Order #${order.id} paid`);
    } catch (reason) {
      if (mounted.current)
        setPaymentActionError(
          apiMessage(reason, "Could not complete this test payment. Please retry."),
        );
    } finally {
      if (mounted.current) setTestPaying(false);
    }
  }

  if (createdOrder) {
    const canPayTest =
      createdPayment?.provider === "test" &&
      activePaymentStatuses.has(createdPayment.status) &&
      createdOrder.payment_status !== "paid";
    const hostedPayment =
      createdPayment &&
      (createdPayment.provider === "payme" || createdPayment.provider === "click");
    return (
      <main className="site-container checkout-page checkout-confirmation">
        <p className="checkout-eyebrow">Order #{createdOrder.id}</p>
        <h1 className="checkout-title">
          {createdOrder.payment_status === "paid" ? "Payment confirmed" : "Your order is saved"}
        </h1>
        <p className="checkout-intro">
          {createdOrder.payment_method === "cash"
            ? "Pay the courier when your flowers arrive."
            : createdOrder.payment_status === "paid"
              ? "View your orders for delivery updates."
              : "Complete your payment below. Your order is also available in your account."}
        </p>
        <div className="checkout-result-facts">
          <div>
            <span>Order status</span>
            <strong>{createdOrder.status_display}</strong>
          </div>
          <div>
            <span>Payment</span>
            <strong>
              {createdOrder.payment_method_display} · {createdOrder.payment_status_display}
            </strong>
          </div>
          <div>
            <span>Total</span>
            <strong>{formatPrice(Number(createdOrder.total_price), currency)}</strong>
          </div>
          <div>
            <span>Delivery</span>
            <strong>
              {createdOrder.delivery_date} ·{" "}
              {createdOrder.delivery_time_slot_display || createdOrder.delivery_time_slot}
            </strong>
          </div>
        </div>
        <p>{createdOrder.delivery_address || createdOrder.shipping_address}</p>
        {createdOrder.delivery_requires_confirmation && (
          <p className="ui-notice">
            Staff will confirm delivery availability and the final fee for this zone.
          </p>
        )}
        {createdOrder.payment_method === "cash" && (
          <p className="ui-notice">Cash on delivery selected. No card payment is required now.</p>
        )}
        {createdPayment?.provider === "test" && (
          <div className="ui-notice">
            <p>
              This is a test payment. No real money will be charged. No card details are needed or
              saved.
            </p>
            {canPayTest && (
              <button
                type="button"
                className="ui-button checkout-action"
                disabled={testPaying}
                onClick={() => void completeTestPayment()}
              >
                {testPaying ? "Completing test payment…" : "Pay test order"}
              </button>
            )}
            {createdOrder.payment_status === "paid" && <p>Test payment complete.</p>}
          </div>
        )}
        {hostedPayment &&
          createdOrder.payment_status !== "paid" &&
          activePaymentStatuses.has(createdPayment.status) &&
          createdPayment.checkout_url && (
            <a className="ui-button checkout-action" href={createdPayment.checkout_url}>
              Continue to {createdPayment.provider}
              <ArrowRightIcon />
            </a>
          )}
        {createdOrder.payment_method !== "cash" &&
          createdOrder.payment_status !== "paid" &&
          !canPayTest &&
          (!createdPayment?.checkout_url || !activePaymentStatuses.has(createdPayment.status)) && (
            <button
              type="button"
              className="ui-button-secondary checkout-action"
              disabled={paymentPreparing}
              onClick={() => void preparePayment(createdOrder, true)}
            >
              {paymentPreparing ? "Preparing secure checkout…" : "Retry secure checkout"}
            </button>
          )}
        {createdPayment?.provider_reference && (
          <p className="checkout-muted checkout-reference">
            Payment ref {createdPayment.provider_reference}
          </p>
        )}
        {paymentActionError && (
          <p className="ui-error" role="alert">
            {paymentActionError}
          </p>
        )}
        <div className="checkout-result-links">
          <Link className="ui-button" href="/profile">
            View my orders
          </Link>
          <Link className="checkout-text-link" href="/#catalog">
            Continue shopping
          </Link>
        </div>
      </main>
    );
  }

  if (!cartLines.length) {
    return (
      <main className="site-container checkout-page checkout-empty">
        <h1 className="checkout-title">Your bag</h1>
        <p>{cartLoading ? "Syncing your bag…" : t.empty}</p>
        {cartError && (
          <p className="ui-error" role="alert">
            {cartError}
          </p>
        )}
        {cartSyncBlocked && user && (
          <button
            className="ui-button-secondary"
            type="button"
            onClick={() => void reloadCart()}
            disabled={cartLoading}
          >
            Retry cart sync
          </button>
        )}
        <Link className="ui-button" href="/#catalog">
          Explore the flowers
          <ArrowRightIcon />
        </Link>
      </main>
    );
  }

  return (
    <main className="site-container checkout-page">
      <form id="checkout-form" onSubmit={submitOrder} className="checkout-layout">
        <section className="checkout-main">
          <h1 className="checkout-title">{checkoutOpen ? "Checkout" : "Your bag"}</h1>
          {checkoutOpen ? (
            <button type="button" className="checkout-back" onClick={() => setCheckoutOpen(false)}>
              <ArrowRightIcon className="checkout-back-arrow" />
              Back to bag
            </button>
          ) : (
            <Link className="checkout-back" href="/#catalog">
              <ArrowRightIcon className="checkout-back-arrow" />
              Continue shopping
            </Link>
          )}
          {(cartError || cartSyncBlocked) && (
            <div className="ui-error" role="alert">
              <p>{cartError || "Sync your saved selections before checkout."}</p>
              <button
                type="button"
                className="checkout-text-link"
                disabled={cartLoading}
                onClick={() => void reloadCart()}
              >
                {cartLoading ? "Syncing…" : "Retry cart sync"}
              </button>
            </div>
          )}
          {mixedFlorists && (
            <div className="ui-notice" role="alert">
              <p>Items from different florists must be checked out separately.</p>
              <p>
                Keep flowers from one florist in your bag to continue. You can remove items below.
              </p>
            </div>
          )}

          {!checkoutOpen || mixedFlorists ? (
            <ul className="checkout-bag-list" aria-label="Flowers in your bag">
              {cartLines.map(({ product, qty }) => (
                <li className="checkout-bag-item" key={product.id}>
                  <Link
                    href={`/product/${product.slug ?? product.id}`}
                    className="checkout-bag-photo"
                  >
                    {product.image ? (
                      <img src={product.image} alt={product.name} />
                    ) : (
                      <BouquetArt palette={product.palette} />
                    )}
                  </Link>
                  <div className="checkout-bag-info">
                    <Link
                      className="checkout-product-name"
                      href={`/product/${product.slug ?? product.id}`}
                    >
                      {product.name}
                    </Link>
                    <p className="checkout-muted">{product.shop}</p>
                    <p>{formatPrice(product.price, currency)}</p>
                    <div className="checkout-quantity">
                      <button
                        type="button"
                        aria-label={`Decrease ${product.name} quantity`}
                        disabled={cartBlocked || submitting}
                        onClick={() => setCartQty(product.id, qty - 1)}
                      >
                        <MinusIcon />
                      </button>
                      <span>{qty}</span>
                      <button
                        type="button"
                        aria-label={`Increase ${product.name} quantity`}
                        disabled={
                          cartBlocked ||
                          submitting ||
                          (product.stock !== undefined && qty >= product.stock)
                        }
                        onClick={() => setCartQty(product.id, qty + 1)}
                      >
                        <PlusIcon />
                      </button>
                    </div>
                  </div>
                  <div className="checkout-bag-end">
                    <strong>{formatPrice(product.price * qty, currency)}</strong>
                    <button
                      type="button"
                      className="checkout-remove"
                      aria-label={`Remove ${product.name} from bag`}
                      disabled={cartBlocked || submitting}
                      onClick={() => removeFromCart(product.id)}
                    >
                      <TrashIcon />
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          ) : null}

          {checkoutOpen && !mixedFlorists && user && (
            <>
              <section className="checkout-section" aria-labelledby="delivery-heading">
                <h2 id="delivery-heading">1. Delivery details</h2>
                <div className="checkout-fields">
                  <label className="checkout-wide">
                    <span className="ui-label">Address</span>
                    <input
                      className="ui-field"
                      required
                      maxLength={500}
                      autoComplete="street-address"
                      value={deliveryLocation.address}
                      onChange={(event) =>
                        setDeliveryLocation({ address: event.target.value, lat: null, lng: null })
                      }
                      placeholder="Street, building, apartment"
                    />
                  </label>
                  <label>
                    <span className="ui-label">Contact phone</span>
                    <input
                      className="ui-field"
                      type="tel"
                      autoComplete="tel"
                      required
                      maxLength={20}
                      value={phone}
                      onChange={(event) => setPhone(event.target.value)}
                      placeholder="+998 90 123 45 67"
                    />
                  </label>
                  <label>
                    <span className="ui-label">Delivery city</span>
                    <select
                      className="ui-field"
                      value={city}
                      onChange={(event) => changeCity(event.target.value)}
                      disabled={submitting}
                    >
                      {!cities.some((item) => item.name === city) && (
                        <option value={city}>{city}</option>
                      )}
                      {cities.map((item) => (
                        <option key={item.id} value={item.name}>
                          {item.name}
                        </option>
                      ))}
                    </select>
                  </label>
                  {citiesError && (
                    <p className="checkout-wide checkout-muted">
                      Could not load other cities.{" "}
                      <button
                        type="button"
                        className="checkout-text-link"
                        onClick={() => setCityAttempt((attempt) => attempt + 1)}
                      >
                        Retry cities
                      </button>
                    </p>
                  )}
                  <label className="checkout-wide">
                    <span className="ui-label">Delivery zone</span>
                    <select
                      className="ui-field"
                      value={selectedZone?.id ?? ""}
                      required
                      disabled={zoneStatus !== "ready" || submitting}
                      onChange={(event) => setSelectedZoneId(Number(event.target.value))}
                    >
                      {zoneStatus !== "ready" && (
                        <option value="">
                          {zoneStatus === "loading"
                            ? "Loading delivery zones…"
                            : "No delivery zone selected"}
                        </option>
                      )}
                      {zonesCurrent &&
                        zoneState.zones.map((zone) => (
                          <option key={zone.id} value={zone.id}>
                            {zone.name}
                          </option>
                        ))}
                    </select>
                  </label>
                  {zoneStatus === "loading" && (
                    <p role="status" className="checkout-wide checkout-muted">
                      Checking available delivery zones for {city}…
                    </p>
                  )}
                  {(zoneStatus === "error" || zoneStatus === "empty") && (
                    <div className="checkout-wide ui-error" role="alert">
                      <p>
                        {zoneStatus === "error"
                          ? "Could not load delivery zones. Retry before placing your order."
                          : `No delivery zones are currently available for ${city}. Choose another city or check again.`}
                      </p>
                      <button type="button" className="checkout-text-link" onClick={retryZones}>
                        Retry delivery zones
                      </button>
                    </div>
                  )}
                  <label>
                    <span className="ui-label">Delivery date</span>
                    <input
                      className="ui-field"
                      type="date"
                      required
                      min={dateInputValue()}
                      value={deliveryDate}
                      onChange={(event) => setDeliveryDate(event.target.value)}
                    />
                  </label>
                  <label>
                    <span className="ui-label">Time slot</span>
                    <select
                      className="ui-field"
                      value={timeSlot}
                      onChange={(event) => setTimeSlot(event.target.value)}
                    >
                      {deliveryTimeSlots.map((slot) => (
                        <option key={slot} value={slot}>
                          {slot}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
                <p className="checkout-muted checkout-slot-note">
                  Delivery availability is confirmed by the florist.
                </p>
                {selectedZone?.description && (
                  <p className="checkout-muted">{selectedZone.description}</p>
                )}
                {selectedZone?.requires_manual_confirmation && (
                  <p className="ui-notice">
                    Staff will confirm delivery availability and the final fee for this zone. The
                    total shown is an estimate.
                  </p>
                )}
                <label className="checkout-check">
                  <input
                    type="checkbox"
                    checked={sendAsGift}
                    onChange={(event) => setSendAsGift(event.target.checked)}
                  />
                  Send to someone else
                </label>
                {sendAsGift && (
                  <div className="checkout-fields checkout-gift-fields">
                    <label>
                      <span className="ui-label">Recipient name</span>
                      <input
                        className="ui-field"
                        required
                        maxLength={150}
                        value={recipientName}
                        onChange={(event) => setRecipientName(event.target.value)}
                      />
                    </label>
                    <label>
                      <span className="ui-label">Recipient phone</span>
                      <input
                        className="ui-field"
                        type="tel"
                        required
                        maxLength={20}
                        value={recipientPhone}
                        onChange={(event) => setRecipientPhone(event.target.value)}
                      />
                    </label>
                    <label className="checkout-check checkout-wide">
                      <input
                        type="checkbox"
                        checked={callRecipient}
                        onChange={(event) => setCallRecipient(event.target.checked)}
                      />
                      Call recipient before delivery
                    </label>
                  </div>
                )}
                <details className="checkout-disclosure">
                  <summary>Gift note &amp; courier instructions</summary>
                  <div className="checkout-fields">
                    <label className="checkout-wide">
                      <span className="ui-label">Gift note (optional)</span>
                      <textarea
                        className="ui-field"
                        rows={3}
                        maxLength={1000}
                        value={giftNote}
                        onChange={(event) => setGiftNote(event.target.value)}
                        placeholder="A little message to send with the flowers"
                      />
                    </label>
                    <label className="checkout-wide">
                      <span className="ui-label">Courier instructions (optional)</span>
                      <textarea
                        className="ui-field"
                        rows={2}
                        maxLength={1000}
                        value={notes}
                        onChange={(event) => setNotes(event.target.value)}
                        placeholder="Entrance, floor, landmark…"
                      />
                    </label>
                  </div>
                </details>
                <button
                  type="button"
                  className="checkout-map-toggle checkout-text-link"
                  aria-expanded={showMap}
                  onClick={() => setShowMap((previous) => !previous)}
                >
                  {showMap ? "Hide map" : "Choose a point on the map"}
                </button>
                {showMap && (
                  <div className="checkout-map">
                    <DeliveryMapPicker value={deliveryLocation} onChange={setDeliveryLocation} />
                  </div>
                )}
              </section>
              <section
                className="checkout-section checkout-payment"
                aria-labelledby="payment-heading"
              >
                <h2 id="payment-heading">2. Payment</h2>
                {paymentLoading && (
                  <p className="checkout-muted" role="status">
                    Checking payment availability…
                  </p>
                )}
                {paymentOptions.map((option) => (
                  <label
                    className={`checkout-payment-option ${option.id === paymentOptionId ? "is-selected" : ""}`}
                    key={option.id}
                  >
                    <input
                      type="radio"
                      name="payment"
                      value={option.id}
                      checked={option.id === paymentOptionId}
                      disabled={!option.enabled || paymentLoading || submitting}
                      onChange={() => setPaymentOptionId(option.id)}
                    />
                    <span>
                      <strong>{option.test_mode ? "Test card payment" : option.label}</strong>
                      <small>
                        {option.test_mode
                          ? "Demo only. No real charge or card details."
                          : option.detail}
                      </small>
                    </span>
                  </label>
                ))}
                {selectedPayment?.test_mode && (
                  <p className="checkout-muted">
                    This is a test payment. No real money will be charged.
                  </p>
                )}
                {selectedPayment &&
                  selectedPayment.provider !== "cash" &&
                  !selectedPayment.test_mode && (
                    <p className="checkout-muted">
                      Card details are entered on the payment provider page and are never stored
                      here.
                    </p>
                  )}
                {paymentError && <p className="ui-notice">{paymentError}</p>}
              </section>
            </>
          )}
        </section>

        <aside className="checkout-summary" aria-labelledby="summary-heading">
          <h2 id="summary-heading">Your order</h2>
          <ul className="checkout-summary-products">
            {cartLines.map(({ product, qty }) => (
              <li key={product.id}>
                {product.image ? (
                  <img src={product.image} alt="" />
                ) : (
                  <div className="checkout-summary-art">
                    <BouquetArt palette={product.palette} />
                  </div>
                )}
                <div>
                  <p className="checkout-summary-name">{product.name}</p>
                  <p className="checkout-muted">{product.shop}</p>
                  <p>
                    {qty} × {formatPrice(product.price, currency)}
                  </p>
                </div>
                <strong>{formatPrice(product.price * qty, currency)}</strong>
              </li>
            ))}
          </ul>
          <dl className="checkout-totals">
            <div>
              <dt>Subtotal</dt>
              <dd>{formatPrice(subtotal, currency)}</dd>
            </div>
            {checkoutOpen && (
              <div>
                <dt>Delivery</dt>
                <dd>
                  {selectedZone?.requires_manual_confirmation
                    ? "To be confirmed"
                    : deliveryFee === null
                      ? "Select a zone"
                      : deliveryFee === 0
                        ? "Free"
                        : formatPrice(deliveryFee, currency)}
                </dd>
              </div>
            )}
            {promoDiscount > 0 && (
              <div>
                <dt>Promo</dt>
                <dd>−{formatPrice(promoDiscount, currency)}</dd>
              </div>
            )}
          </dl>
          {checkoutOpen && user && (
            <div className="checkout-promo">
              <label htmlFor="checkout-promo" className="ui-label">
                Promo code
              </label>
              <div>
                <input
                  id="checkout-promo"
                  className="ui-field"
                  value={promoCode}
                  maxLength={40}
                  onChange={(event) => {
                    setPromoCode(event.target.value);
                    setPromoError("");
                  }}
                  placeholder="Enter code"
                />
                <button
                  className="ui-button-secondary"
                  type="button"
                  disabled={promoLoading || submitting}
                  onClick={() => void applyPromo()}
                >
                  {promoLoading ? "Applying…" : "Apply"}
                </button>
              </div>
              {promoNeedsRefresh && !promoError && (
                <p className="checkout-muted">Apply the code to update your total, or clear it.</p>
              )}
              {promoError && (
                <p className="ui-error" role="alert">
                  {promoError}
                </p>
              )}
            </div>
          )}
          <div className="checkout-grand-total">
            <span>
              {checkoutOpen
                ? selectedZone?.requires_manual_confirmation
                  ? "Estimated total"
                  : "Total"
                : "Subtotal"}
            </span>
            <strong>{formatPrice(checkoutOpen ? total : subtotal, currency)}</strong>
          </div>
          {error && (
            <p className="ui-error" role="alert">
              {error}
            </p>
          )}
          {!user ? (
            <>
              <p className="checkout-muted">Sign in to arrange delivery. Your bag will be saved.</p>
              <Link
                className="ui-button checkout-submit"
                href="/profile?mode=login&next=%2Fcheckout"
              >
                Sign in to continue
                <ArrowRightIcon />
              </Link>
            </>
          ) : !checkoutOpen || mixedFlorists ? (
            <button
              className="ui-button checkout-submit"
              type="button"
              disabled={cartBlocked || mixedFlorists}
              onClick={() => {
                setError("");
                setCheckoutOpen(true);
              }}
            >
              Continue to checkout
              <ArrowRightIcon />
            </button>
          ) : (
            <button className="ui-button checkout-submit" type="submit" disabled={!canSubmit}>
              {submitting
                ? "Placing order…"
                : selectedPayment?.test_mode
                  ? "Place test order"
                  : selectedPayment?.provider === "cash"
                    ? "Place cash order"
                    : "Continue to card payment"}
              <ArrowRightIcon />
            </button>
          )}
          <p className="checkout-muted checkout-summary-note">
            {checkoutOpen
              ? "Prices and stock are checked when you place the order."
              : "Delivery and payment options are available at checkout."}
          </p>
        </aside>
      </form>
    </main>
  );
}
