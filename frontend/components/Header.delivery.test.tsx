// @vitest-environment jsdom
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { createOrder, fetchCities, fetchDeliveryZones, fetchPaymentConfiguration } from "@/lib/api";
import { products } from "@/lib/data";
import { useStore } from "@/lib/store";
import Header from "./Header";

vi.mock("@/lib/store", () => ({
  useStore: vi.fn(),
  usePriceFormatter: () => (value: number) => String(value),
}));
vi.mock("@/lib/api", async (original) => ({
  ...(await original<typeof import("@/lib/api")>()),
  createOrder: vi.fn(),
  fetchCities: vi.fn(),
  fetchDeliveryZones: vi.fn(),
  fetchPaymentConfiguration: vi.fn(),
}));
vi.mock("./DeliveryMapPicker", () => ({ default: () => null }));

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.stubGlobal(
    "matchMedia",
    vi.fn(() => ({ matches: false })),
  );
  vi.mocked(useStore).mockReturnValue({
    user: { id: 1, username: "QA buyer", address: "Isolated QA address", phone: "QA-only-phone" },
    name: "QA buyer",
    cartCount: 1,
    hydrated: true,
    language: "EN",
    currency: "USD",
    city: "Tashkent",
    cartLines: [{ product: products[0], qty: 1, subtotal: 10 }],
    cartLoading: false,
    cartSyncBlocked: false,
    cartError: "",
    syncPaymentRate: vi.fn(),
    showToast: vi.fn(),
    clearCart: vi.fn(),
  } as unknown as ReturnType<typeof useStore>);
  vi.mocked(fetchCities).mockResolvedValue([]);
  vi.mocked(fetchDeliveryZones).mockResolvedValue([]);
  vi.mocked(fetchPaymentConfiguration).mockResolvedValue({
    uzs_per_price_unit: "12650",
    methods: [
      {
        id: "cash",
        payment_method: "cash",
        provider: "cash",
        label: "Cash",
        detail: "",
        enabled: true,
        test_mode: false,
      },
    ],
  });
  vi.mocked(createOrder).mockRejectedValue(new Error("QA stops after checking the request"));
});

afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.unstubAllGlobals();
  vi.resetAllMocks();
});

async function openCheckout() {
  render(<Header />);
  fireEvent.click(screen.getByRole("button", { name: "Cart (1 items)" }));
  fireEvent.click(screen.getByRole("button", { name: "Checkout" }));
  const submit = await screen.findByRole("button", { name: "Place cash order" });
  await waitFor(() => expect((submit as HTMLButtonElement).disabled).toBe(false));
  return submit.closest("form")!;
}

it("requires another window if the chosen delivery window ends before submission", async () => {
  vi.setSystemTime(new Date("2026-11-16T11:59:59+05:00"));
  const form = await openCheckout();
  const time = screen.getByRole("combobox", { name: "Delivery time" });
  fireEvent.change(time, { target: { value: "09:00-12:00" } });

  vi.setSystemTime(new Date("2026-11-16T12:00:00+05:00"));
  fireEvent.submit(form);
  expect(createOrder).not.toHaveBeenCalled();
  expect(screen.getAllByText("Choose a delivery date and time slot.").length).toBeGreaterThan(0);
  expect((time as HTMLSelectElement).value).toBe("");

  fireEvent.change(time, { target: { value: "12:00-15:00" } });
  await act(async () => fireEvent.submit(form));
  expect(createOrder).toHaveBeenCalledWith(
    expect.objectContaining({ delivery_date: "2026-11-16", delivery_time_slot: "12:00-15:00" }),
  );
});

it("opens checkout on tomorrow after the last Tashkent window has ended", async () => {
  vi.setSystemTime(new Date("2026-11-16T21:00:00+05:00"));
  await openCheckout();
  expect((screen.getByRole("combobox", { name: "Delivery day" }) as HTMLSelectElement).value).toBe(
    "tomorrow",
  );
  expect((screen.getByRole("option", { name: "Today" }) as HTMLOptionElement).disabled).toBe(true);
  expect((screen.getByRole("combobox", { name: "Delivery time" }) as HTMLSelectElement).value).toBe(
    "12:00-15:00",
  );
});
