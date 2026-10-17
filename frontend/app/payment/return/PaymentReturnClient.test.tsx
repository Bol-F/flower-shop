// @vitest-environment jsdom

import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, OfflineError } from "@/lib/api";
import PaymentReturnClient from "./PaymentReturnClient";

const mocks = vi.hoisted(() => ({ fetchPayment: vi.fn() }));
vi.mock("@/lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/lib/api")>()),
  fetchPayment: mocks.fetchPayment,
}));

const payment = {
  id: "payment-1",
  order_id: 12,
  provider: "payme",
  amount: "100000.00",
  currency: "UZS",
  status: "paid",
};

describe("payment confirmation", () => {
  beforeEach(() => {
    mocks.fetchPayment.mockReset();
  });
  afterEach(() => {
    cleanup();
  });

  it("confirms payment only from the backend response", async () => {
    mocks.fetchPayment.mockResolvedValue({ ...payment, status: "pending" });
    window.history.replaceState(null, "", "/payment/return?status=success");
    render(<PaymentReturnClient orderId={12} paymentId="payment-1" />);
    expect(await screen.findByRole("heading", { name: "Payment is processing" })).toBeVisible();
    expect(screen.queryByText("Payment confirmed")).not.toBeInTheDocument();
  });

  it("lets the customer retry a failed status check without creating a payment", async () => {
    mocks.fetchPayment.mockRejectedValueOnce(new OfflineError()).mockResolvedValueOnce(payment);
    render(<PaymentReturnClient orderId={12} paymentId="payment-1" />);
    fireEvent.click(await screen.findByRole("button", { name: "Check again" }));
    expect(await screen.findByRole("heading", { name: "Payment confirmed" })).toBeVisible();
    expect(mocks.fetchPayment).toHaveBeenCalledTimes(2);
    expect(mocks.fetchPayment).toHaveBeenLastCalledWith(12, "payment-1");
  });

  it("offers sign-in when the order cannot be checked without authentication", async () => {
    mocks.fetchPayment.mockRejectedValue(new ApiError(401, { detail: "Authentication required." }));
    render(<PaymentReturnClient orderId={12} paymentId="payment-1" />);
    expect(await screen.findByRole("link", { name: "Sign in" })).toHaveAttribute(
      "href",
      "/profile?mode=login",
    );
    expect(screen.queryByRole("button", { name: "Check again" })).not.toBeInTheDocument();
  });

  it("does not request a payment for invalid order identifiers", async () => {
    render(<PaymentReturnClient orderId={-1} paymentId="payment-1" />);
    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("incomplete"));
    expect(mocks.fetchPayment).not.toHaveBeenCalled();
  });
});
