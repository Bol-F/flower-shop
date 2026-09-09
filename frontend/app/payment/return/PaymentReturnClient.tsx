"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { fetchPayment, type ApiPaymentAttempt } from "@/lib/api";

export function paymentStateCopy(payment: ApiPaymentAttempt | null) {
  if (!payment) return { title: "Confirming your payment", tone: "pending" as const };
  if (payment.status === "paid") return { title: "Payment confirmed", tone: "success" as const };
  if (["failed", "cancelled", "refunded"].includes(payment.status)) {
    return { title: payment.status === "refunded" ? "Payment refunded" : "Payment not completed", tone: "error" as const };
  }
  return { title: "Payment is processing", tone: "pending" as const };
}

export default function PaymentReturnClient({ orderId, paymentId }: { orderId: number; paymentId: string }) {
  const [payment, setPayment] = useState<ApiPaymentAttempt | null>(null);
  const [failure, setFailure] = useState("");

  useEffect(() => {
    if (!orderId || !paymentId) return;
    let active = true;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let attempts = 0;
    const poll = async () => {
      try {
        const latest = await fetchPayment(orderId, paymentId);
        if (!active) return;
        setPayment(latest);
        if (["paid", "failed", "cancelled", "refunded"].includes(latest.status)) return;
        attempts += 1;
        if (attempts < 30) timer = setTimeout(() => void poll(), 2000);
        else setFailure("The provider has not confirmed the payment yet. You can check again from your orders.");
      } catch (reason) {
        if (active) setFailure(reason instanceof Error ? reason.message : "Could not check payment status.");
      }
    };
    void poll();
    return () => {
      active = false;
      if (timer) clearTimeout(timer);
    };
  }, [orderId, paymentId]);

  const copy = paymentStateCopy(payment);
  const displayFailure =
    failure || (!orderId || !paymentId ? "This return link is incomplete." : "");
  return (
    <section className="mx-auto max-w-xl rounded-[2rem] border border-line bg-white p-7 text-center shadow-lift sm:p-10" aria-live="polite">
      <div className={`mx-auto grid size-16 place-items-center rounded-full text-2xl ${copy.tone === "success" ? "bg-mint text-leaf" : copy.tone === "error" ? "bg-berrysoft text-berry" : "bg-blush text-blossomdeep"}`}>
        {copy.tone === "success" ? "✓" : copy.tone === "error" ? "×" : "…"}
      </div>
      <p className="mt-5 text-xs font-extrabold uppercase tracking-[0.2em] text-blossomdeep">Order #{orderId || "—"}</p>
      <h1 className="mt-2 font-display text-3xl font-extrabold text-ink">{displayFailure || copy.title}</h1>
      <p className="mt-3 text-sm font-semibold leading-6 text-stone">
        Status comes directly from the verified provider callback. Closing or refreshing this page will not create another charge.
      </p>
      {payment && (
        <div className="mt-6 grid grid-cols-2 gap-3 rounded-2xl bg-paper p-4 text-left text-sm">
          <span className="font-semibold text-stone">Provider</span><span className="text-right font-extrabold capitalize text-ink">{payment.provider}</span>
          <span className="font-semibold text-stone">Amount</span><span className="text-right font-extrabold text-ink">{payment.amount} {payment.currency}</span>
          <span className="font-semibold text-stone">Status</span><span className="text-right font-extrabold capitalize text-ink">{payment.status}</span>
        </div>
      )}
      <div className="mt-7 flex flex-wrap justify-center gap-3">
        <Link href="/profile" className="rounded-full bg-blossomdeep px-6 py-3 text-sm font-extrabold text-white shadow-glow">View my orders</Link>
        <Link href="/" className="rounded-full border border-line px-6 py-3 text-sm font-extrabold text-stone">Continue shopping</Link>
      </div>
    </section>
  );
}
