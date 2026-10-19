// @vitest-environment jsdom

import "@testing-library/jest-dom/vitest";
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { ApiDeliveryZone, ApiOrder, ApiPaymentAttempt, AuthUser } from "@/lib/api";
import type { CartLine } from "@/lib/store";
import type { Product } from "@/lib/types";
import CheckoutClient from "./CheckoutClient";

const mocks = vi.hoisted(() => ({
  state: {} as Record<string, unknown>,
  createOrder: vi.fn(),
  fetchCities: vi.fn(),
  fetchDeliveryZones: vi.fn(),
  fetchPaymentConfiguration: vi.fn(),
  initializePayment: vi.fn(),
  payTestOrder: vi.fn(),
  validatePromoCode: vi.fn(),
  clearCart: vi.fn(),
  reloadCart: vi.fn(),
  setCartQty: vi.fn(),
  removeFromCart: vi.fn(),
  syncPaymentRate: vi.fn(),
  showToast: vi.fn(),
}));

vi.mock("@/lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/lib/api")>()),
  createOrder: mocks.createOrder,
  fetchCities: mocks.fetchCities,
  fetchDeliveryZones: mocks.fetchDeliveryZones,
  fetchPaymentConfiguration: mocks.fetchPaymentConfiguration,
  initializePayment: mocks.initializePayment,
  payTestOrder: mocks.payTestOrder,
  validatePromoCode: mocks.validatePromoCode,
}));
vi.mock("@/lib/store", () => ({
  useStore: () => mocks.state,
  usePriceFormatter: () => (amount: number) => `$${amount.toFixed(2)}`,
}));
vi.mock("./DeliveryMapPicker", () => ({
  default: ({
    onChange,
  }: {
    onChange: (value: { address: string; lat: number; lng: number }) => void;
  }) => (
    <button
      type="button"
      onClick={() => onChange({ address: "Pinned address", lat: 41.3, lng: 69.2 })}
    >
      Use selected map point
    </button>
  ),
}));

const user: AuthUser = {
  id: 1,
  username: "Customer",
  email: "customer@example.test",
  phone: "+998901234567",
  address: "Main Street 12",
  bio: "",
  city: "Tashkent",
  language: "EN",
  currency: "USD",
  loyalty_points: 0,
  is_staff: false,
  date_joined: "2026-01-01",
};
const product: Product = {
  id: "roses",
  backendId: 1,
  slug: "roses",
  name: "Rose Bouquet",
  shop: "First florist",
  vendor: "first-florist",
  price: 20,
  category: "roses",
  rating: null,
  reviews: 0,
  deliveryMins: null,
  deliveryToday: null,
  isNew: false,
  popularity: 0,
  description: "Roses",
  composition: [],
  hasSizes: false,
  palette: { petals: ["#fff"], center: "#ddd", backdrop: "#eee" },
  stock: 5,
  isAvailable: true,
  isInStock: true,
  source: "api",
};
const zone: ApiDeliveryZone = {
  id: 10,
  name: "Tashkent Center",
  city: "Tashkent",
  city_slug: "tashkent",
  fee: "2.37",
  free_delivery_threshold: "100.00",
  is_active: true,
  requires_manual_confirmation: false,
  description: "Central delivery.",
};
const cashMethod = {
  id: "cash",
  payment_method: "cash",
  provider: "cash",
  label: "Cash on delivery",
  detail: "Pay the courier",
  enabled: true,
  test_mode: false,
};
const testMethod = {
  id: "test",
  payment_method: "card",
  provider: "test",
  label: "Pay by card",
  detail: "Test only",
  enabled: true,
  test_mode: true,
};
const payment: ApiPaymentAttempt = {
  id: "bcb75105-619b-4adf-94bc-59fb0e639898",
  order_id: 41,
  provider: "test",
  amount: "282980.50",
  currency: "UZS",
  status: "pending",
  checkout_url: "",
  provider_reference: "TEST-41",
  failure_code: "",
  failure_message: "",
  paid_at: null,
  created_at: "2026-10-19",
  updated_at: "2026-10-19",
};
const order: ApiOrder = {
  id: 41,
  status: "pending",
  status_display: "Pending",
  status_timeline: [],
  user_email: user.email,
  user_username: user.username,
  city_name: "Tashkent",
  city_slug: "tashkent",
  vendor_name: product.shop,
  vendor_slug: product.vendor!,
  subtotal_price: "20.00",
  total_price: "22.37",
  shipping_address: user.address,
  phone: user.phone,
  payment_method: "cash",
  payment_method_display: "Cash",
  payment_status: "unpaid",
  payment_status_display: "Unpaid",
  payment_provider: "cash",
  payment_reference: "",
  paid_at: null,
  promo_code: null,
  discount_amount: "0.00",
  loyalty_points_earned: 0,
  delivery_address: user.address,
  delivery_lat: null,
  delivery_lng: null,
  delivery_date: "2026-10-20",
  delivery_time_slot: "12:00-15:00",
  delivery_time_slot_display: "12:00-15:00",
  delivery_zone: zone,
  delivery_requires_confirmation: false,
  assigned_courier_id: null,
  assigned_courier_name: null,
  courier_assigned_at: null,
  courier_picked_up_at: null,
  delivered_at: null,
  recipient_name: user.username,
  recipient_phone: user.phone,
  gift_note: "",
  call_recipient_before_delivery: false,
  delivery_fee: "2.37",
  notes: "",
  items: [],
  notification_logs: [],
  latest_payment: null,
  created_at: "2026-10-19",
  updated_at: "2026-10-19",
};

function line(item = product, qty = 1): CartLine {
  return { product: item, qty, subtotal: item.price * qty };
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (error: Error) => void;
  const promise = new Promise<T>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
}

async function openCheckout() {
  fireEvent.click(screen.getByRole("button", { name: "Continue to checkout" }));
  await waitFor(() =>
    expect(screen.getByRole("button", { name: "Place cash order" })).toBeEnabled(),
  );
}

describe("full-page bag and checkout", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.state = {
      hydrated: true,
      user,
      cartLines: [line()],
      currency: "USD",
      language: "EN",
      city: "Tashkent",
      setCity: (city: string) => {
        mocks.state.city = city;
      },
      setCartQty: mocks.setCartQty,
      removeFromCart: mocks.removeFromCart,
      clearCart: mocks.clearCart,
      cartLoading: false,
      cartSyncBlocked: false,
      cartError: "",
      reloadCart: mocks.reloadCart,
      showToast: mocks.showToast,
      syncPaymentRate: mocks.syncPaymentRate,
    };
    mocks.fetchCities.mockResolvedValue([
      { id: 1, name: "Tashkent", slug: "tashkent", is_active: true },
      { id: 2, name: "Samarkand", slug: "samarkand", is_active: true },
    ]);
    mocks.fetchDeliveryZones.mockResolvedValue([zone]);
    mocks.fetchPaymentConfiguration.mockResolvedValue({
      methods: [cashMethod, testMethod],
      uzs_per_price_unit: "12650",
    });
    mocks.createOrder.mockResolvedValue(order);
    mocks.initializePayment.mockResolvedValue(payment);
    mocks.payTestOrder.mockResolvedValue({
      ...order,
      payment_method: "card",
      payment_provider: "test",
      payment_status: "paid",
      payment_status_display: "Paid",
      latest_payment: { ...payment, status: "paid" },
    });
    mocks.validatePromoCode.mockResolvedValue({ code: "FLOWER", discount_amount: "2.00" });
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("waits for hydration and preserves the sign-in return destination for guests", () => {
    mocks.state.hydrated = false;
    const view = render(<CheckoutClient />);
    expect(screen.getByRole("status")).toHaveTextContent("Loading your saved selections");
    expect(mocks.fetchDeliveryZones).not.toHaveBeenCalled();
    mocks.state.hydrated = true;
    mocks.state.user = null;
    view.rerender(<CheckoutClient />);
    expect(screen.getByRole("link", { name: "Sign in to continue" })).toHaveAttribute(
      "href",
      "/profile?mode=login&next=%2Fcheckout",
    );
    expect(mocks.createOrder).not.toHaveBeenCalled();
  });

  it("keeps quantity/removal controls and blocks checkout during unresolved cart sync", () => {
    mocks.state.cartSyncBlocked = true;
    mocks.state.cartError = "Selections need synchronization.";
    const view = render(<CheckoutClient />);
    expect(screen.getByRole("button", { name: "Continue to checkout" })).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "Retry cart sync" }));
    expect(mocks.reloadCart).toHaveBeenCalledOnce();
    mocks.state.cartSyncBlocked = false;
    mocks.state.cartError = "";
    view.rerender(<CheckoutClient />);
    fireEvent.click(screen.getByRole("button", { name: "Increase Rose Bouquet quantity" }));
    expect(mocks.setCartQty).toHaveBeenCalledWith("roses", 2);
    fireEvent.click(screen.getByRole("button", { name: "Remove Rose Bouquet from bag" }));
    expect(mocks.removeFromCart).toHaveBeenCalledWith("roses");
  });

  it("explains multiple florists before the form and does not create an order", () => {
    mocks.state.cartLines = [
      line(),
      line({
        ...product,
        id: "tulips",
        name: "Tulips",
        vendor: "second-florist",
        shop: "Second florist",
      }),
    ];
    render(<CheckoutClient />);
    expect(screen.getByRole("alert")).toHaveTextContent("Items from different florists");
    expect(screen.getByRole("button", { name: "Continue to checkout" })).toBeDisabled();
    expect(screen.queryByRole("heading", { name: "1. Delivery details" })).not.toBeInTheDocument();
    expect(mocks.createOrder).not.toHaveBeenCalled();
  });

  it.each(["error", "empty"])(
    "blocks %s zone responses until a real API zone is loaded on retry",
    async (state) => {
      if (state === "error") mocks.fetchDeliveryZones.mockRejectedValueOnce(new Error("offline"));
      else mocks.fetchDeliveryZones.mockResolvedValueOnce([]);
      const pending = deferred<ApiDeliveryZone[]>();
      mocks.fetchDeliveryZones.mockReturnValueOnce(pending.promise);
      render(<CheckoutClient />);
      fireEvent.click(screen.getByRole("button", { name: "Continue to checkout" }));
      await screen.findByRole("button", { name: "Retry delivery zones" });
      expect(screen.getByRole("button", { name: "Place cash order" })).toBeDisabled();
      fireEvent.click(screen.getByRole("button", { name: "Retry delivery zones" }));
      expect(screen.getByRole("button", { name: "Place cash order" })).toBeDisabled();
      expect(screen.getByLabelText("Delivery zone")).toBeDisabled();
      await act(async () => pending.resolve([zone]));
      await waitFor(() =>
        expect(screen.getByRole("button", { name: "Place cash order" })).toBeEnabled(),
      );
      expect(screen.getByLabelText("Delivery zone")).toHaveValue("10");
    },
  );

  it("clears a previous city selection immediately and ignores its late response", async () => {
    const oldRequest = deferred<ApiDeliveryZone[]>();
    const newRequest = deferred<ApiDeliveryZone[]>();
    mocks.fetchDeliveryZones
      .mockReturnValueOnce(oldRequest.promise)
      .mockReturnValueOnce(newRequest.promise);
    render(<CheckoutClient />);
    fireEvent.click(screen.getByRole("button", { name: "Continue to checkout" }));
    await screen.findByRole("option", { name: "Samarkand" });
    fireEvent.change(screen.getByLabelText("Delivery city"), { target: { value: "Samarkand" } });
    expect(screen.getByRole("button", { name: "Place cash order" })).toBeDisabled();
    await act(async () => oldRequest.resolve([zone]));
    expect(screen.queryByRole("option", { name: "Tashkent Center" })).not.toBeInTheDocument();
    await act(async () =>
      newRequest.resolve([
        { ...zone, id: 22, name: "Samarkand Center", city: "Samarkand", city_slug: "samarkand" },
      ]),
    );
    expect(screen.getByLabelText("Delivery zone")).toHaveValue("22");
    fireEvent.click(screen.getByRole("button", { name: "Place cash order" }));
    await waitFor(() =>
      expect(mocks.createOrder).toHaveBeenCalledWith(
        expect.objectContaining({ city_slug: "samarkand", delivery_zone_id: 22 }),
      ),
    );
  });

  it("rejects bundled/nonpositive and wrong-city zone IDs", async () => {
    mocks.fetchDeliveryZones.mockResolvedValue([
      { ...zone, id: -1 },
      { ...zone, id: 23, city_slug: "other-city" },
    ]);
    render(<CheckoutClient />);
    fireEvent.click(screen.getByRole("button", { name: "Continue to checkout" }));
    await screen.findByRole("button", { name: "Retry delivery zones" });
    expect(screen.getByRole("button", { name: "Place cash order" })).toBeDisabled();
    expect(screen.queryByRole("option", { name: "Tashkent Center" })).not.toBeInTheDocument();
  });

  it("submits the real zone, gift/map/promo fields and keeps confirmation after local-only clearing", async () => {
    const view = render(<CheckoutClient />);
    await openCheckout();
    fireEvent.click(screen.getByLabelText("Send to someone else"));
    fireEvent.change(screen.getByLabelText("Recipient name"), { target: { value: "Friend" } });
    fireEvent.change(screen.getByLabelText("Recipient phone"), {
      target: { value: "+998909999999" },
    });
    fireEvent.click(screen.getByText("Gift note & courier instructions"));
    fireEvent.change(screen.getByLabelText("Gift note (optional)"), {
      target: { value: "Happy birthday" },
    });
    fireEvent.change(screen.getByLabelText("Courier instructions (optional)"), {
      target: { value: "Second floor" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Choose a point on the map" }));
    fireEvent.click(screen.getByRole("button", { name: "Use selected map point" }));
    fireEvent.change(screen.getByLabelText("Promo code"), { target: { value: "flower" } });
    fireEvent.click(screen.getByRole("button", { name: "Apply" }));
    await waitFor(() => expect(screen.getByLabelText("Promo code")).toHaveValue("FLOWER"));
    fireEvent.click(screen.getByRole("button", { name: "Place cash order" }));
    await waitFor(() =>
      expect(mocks.createOrder).toHaveBeenCalledWith(
        expect.objectContaining({
          delivery_zone_id: 10,
          city_slug: "tashkent",
          delivery_address: "Pinned address",
          delivery_lat: 41.3,
          delivery_lng: 69.2,
          recipient_name: "Friend",
          recipient_phone: "+998909999999",
          gift_note: "Happy birthday",
          call_recipient_before_delivery: true,
          notes: "Second floor",
          promo_code: "FLOWER",
          payment_method: "cash",
        }),
      ),
    );
    expect(mocks.clearCart).toHaveBeenCalledExactlyOnceWith({ remote: false });
    mocks.state.cartLines = [];
    view.rerender(<CheckoutClient />);
    expect(screen.getByRole("heading", { name: "Your order is saved" })).toBeInTheDocument();
    expect(screen.getByText("$22.37")).toBeInTheDocument();
    expect(mocks.initializePayment).not.toHaveBeenCalled();
  });

  it("does not advertise provisional manual-confirmation delivery as free", async () => {
    mocks.fetchDeliveryZones.mockResolvedValue([
      { ...zone, fee: "0.00", requires_manual_confirmation: true },
    ]);
    render(<CheckoutClient />);
    await openCheckout();
    expect(screen.getByText("To be confirmed")).toBeInTheDocument();
    expect(screen.getByText("Estimated total")).toBeInTheDocument();
    expect(screen.queryByText("Free")).not.toBeInTheDocument();
  });

  it("resumes the initial test attempt and explicitly completes a no-charge payment", async () => {
    mocks.createOrder.mockResolvedValue({
      ...order,
      payment_method: "card",
      payment_method_display: "Card",
      payment_provider: "test",
      payment_status: "pending",
      payment_status_display: "Pending",
      latest_payment: payment,
    });
    render(<CheckoutClient />);
    await openCheckout();
    fireEvent.click(screen.getByRole("radio", { name: /Test card payment/ }));
    expect(
      screen.getByText("This is a test payment. No real money will be charged."),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Place test order" }));
    const payButton = await screen.findByRole("button", { name: "Pay test order" });
    expect(mocks.initializePayment).not.toHaveBeenCalled();
    fireEvent.click(payButton);
    await screen.findByRole("heading", { name: "Payment confirmed" });
    expect(mocks.payTestOrder).toHaveBeenCalledExactlyOnceWith(41);
    expect(screen.getByText("Test payment complete.")).toBeInTheDocument();
  });

  it("retains the order after hosted initialization failure and retries without another order", async () => {
    mocks.fetchPaymentConfiguration.mockResolvedValue({
      methods: [
        cashMethod,
        { ...testMethod, id: "payme", provider: "payme", detail: "Payme", test_mode: false },
      ],
      uzs_per_price_unit: "12650",
    });
    mocks.createOrder.mockResolvedValue({
      ...order,
      payment_method: "card",
      payment_provider: "payme",
      payment_status: "pending",
      latest_payment: null,
    });
    mocks.initializePayment
      .mockRejectedValueOnce(new Error("Provider unavailable"))
      .mockResolvedValueOnce({
        ...payment,
        provider: "payme",
        checkout_url: "https://checkout.example.test/41",
      });
    render(<CheckoutClient />);
    await openCheckout();
    fireEvent.click(screen.getByRole("radio", { name: /Pay by card/ }));
    fireEvent.click(screen.getByRole("button", { name: "Continue to card payment" }));
    await screen.findByText("Provider unavailable");
    fireEvent.click(screen.getByRole("button", { name: "Retry secure checkout" }));
    const continuation = await screen.findByRole("link", { name: "Continue to payme" });
    expect(continuation).toHaveAttribute("href", "https://checkout.example.test/41");
    expect(mocks.createOrder).toHaveBeenCalledOnce();
    expect(mocks.initializePayment).toHaveBeenCalledTimes(2);
  });

  it("resets profile defaults and unfinished form state when the account changes", async () => {
    const view = render(<CheckoutClient />);
    await openCheckout();
    fireEvent.change(screen.getByLabelText("Contact phone"), {
      target: { value: "Changed draft" },
    });
    mocks.state.user = { ...user, id: 2, phone: "+998900000002", address: "Other address" };
    view.rerender(<CheckoutClient />);
    await openCheckout();
    expect(screen.getByLabelText("Contact phone")).toHaveValue("+998900000002");
    expect(screen.getByLabelText("Address")).toHaveValue("Other address");
    expect(mocks.createOrder).not.toHaveBeenCalled();
  });
});
