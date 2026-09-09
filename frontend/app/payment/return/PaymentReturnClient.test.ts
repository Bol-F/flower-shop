import { describe, expect, it } from "vitest";
import { paymentStateCopy } from "./PaymentReturnClient";
import type { ApiPaymentAttempt } from "@/lib/api";

function payment(status: ApiPaymentAttempt["status"]): ApiPaymentAttempt {
  return {
    id: "payment-id",
    order_id: 1,
    provider: "payme",
    amount: "1000.00",
    currency: "UZS",
    status,
    checkout_url: "",
    provider_reference: "",
    failure_code: "",
    failure_message: "",
    paid_at: null,
    created_at: "",
    updated_at: "",
  };
}

describe("paymentStateCopy", () => {
  it("keeps redirect and processing states pending", () => {
    expect(paymentStateCopy(null).tone).toBe("pending");
    expect(paymentStateCopy(payment("processing")).tone).toBe("pending");
  });

  it("only presents backend-paid attempts as successful", () => {
    expect(paymentStateCopy(payment("paid")).tone).toBe("success");
    expect(paymentStateCopy(payment("failed")).tone).toBe("error");
    expect(paymentStateCopy(payment("cancelled")).tone).toBe("error");
  });
});
