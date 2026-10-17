"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ApiError, fetchPayment, type ApiPaymentAttempt } from "@/lib/api";

export function paymentStateCopy(payment: ApiPaymentAttempt | null) {
  if (!payment) return { title: "Confirming your payment", tone: "pending" as const };
  if (payment.status === "paid") return { title: "Payment confirmed", tone: "success" as const };
  if (["failed", "cancelled", "refunded"].includes(payment.status)) {
    return {
      title: payment.status === "refunded" ? "Payment refunded" : "Payment not completed",
      tone: "error" as const,
    };
  }
  return { title: "Payment is processing", tone: "pending" as const };
}

export default function PaymentReturnClient({
  orderId,
  paymentId,
}: {
  orderId: number;
  paymentId: string;
}) {
  const [payment, setPayment] = useState<ApiPaymentAttempt | null>(null);
  const [failure, setFailure] = useState<{ message: string; requiresLogin: boolean } | null>(null);
  const [checkAttempt, setCheckAttempt] = useState(0);
  const [checking, setChecking] = useState(true);
  const validLink = Number.isSafeInteger(orderId) && orderId > 0 && Boolean(paymentId);

  useEffect(() => {
    if (!validLink) return;
    let active = true;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let attempts = 0;
    const poll = async () => {
      try {
        const latest = await fetchPayment(orderId, paymentId);
        if (!active) return;
        setPayment(latest);
        setChecking(false);
        if (["paid", "failed", "cancelled", "refunded"].includes(latest.status)) return;
        attempts += 1;
        if (attempts < 30) timer = setTimeout(() => void poll(), 2000);
        else
          setFailure({
            message:
              "Your payment is still awaiting confirmation. Check again or view your orders.",
            requiresLogin: false,
          });
      } catch (reason) {
        if (!active) return;
        setChecking(false);
        const requiresLogin = reason instanceof ApiError && reason.status === 401;
        setFailure({
          message: requiresLogin
            ? "Sign in to see the payment status for this order."
            : "We couldn’t check your payment. Please try again.",
          requiresLogin,
        });
      }
    };
    void poll();
    return () => {
      active = false;
      if (timer) clearTimeout(timer);
    };
  }, [orderId, paymentId, validLink, checkAttempt]);

  const copy = paymentStateCopy(payment);
  const displayFailure = failure?.message || (!validLink ? "This return link is incomplete." : "");
  return (
    <section
      className="mx-auto max-w-xl rounded-[2rem] border border-line bg-white p-7 text-center shadow-lift sm:p-10"
      aria-live="polite"
    >
      <div
        className={`mx-auto grid size-16 place-items-center rounded-full text-2xl ${copy.tone === "success" ? "bg-mint text-leaf" : copy.tone === "error" ? "bg-berrysoft text-berry" : "bg-blush text-blossomdeep"}`}
      >
        {copy.tone === "success" ? "✓" : copy.tone === "error" ? "×" : "…"}
      </div>
      <p className="mt-5 text-xs font-extrabold uppercase tracking-[0.2em] text-blossomdeep">
        Order #{orderId || "—"}
      </p>
      <h1 className="mt-2 font-display text-3xl font-extrabold text-ink">
        {validLink ? copy.title : "Payment link unavailable"}
      </h1>
      <p className="mt-3 text-sm font-semibold leading-6 text-stone">
        {copy.tone === "success"
          ? "Your order has been updated. View your orders for delivery details."
          : copy.tone === "error"
            ? "View your orders for details and available next steps."
            : "You can close this page safely. We’ll update your order as soon as your payment is confirmed."}
      </p>
      {displayFailure && (
        <p role="alert" className="mt-4 rounded-2xl bg-paper p-4 text-sm font-semibold text-stone">
          {displayFailure}
        </p>
      )}
      {payment && (
        <div className="mt-6 grid grid-cols-2 gap-3 rounded-2xl bg-paper p-4 text-left text-sm">
          <span className="font-semibold text-stone">Provider</span>
          <span className="text-right font-extrabold capitalize text-ink">{payment.provider}</span>
          <span className="font-semibold text-stone">Amount</span>
          <span className="text-right font-extrabold text-ink">
            {payment.amount} {payment.currency}
          </span>
          <span className="font-semibold text-stone">Status</span>
          <span className="text-right font-extrabold capitalize text-ink">{payment.status}</span>
        </div>
      )}
      <div className="mt-7 flex flex-wrap justify-center gap-3">
        {validLink && failure && !failure.requiresLogin && (
          <button
            type="button"
            disabled={checking}
            onClick={() => {
              setFailure(null);
              setChecking(true);
              setCheckAttempt((attempt) => attempt + 1);
            }}
            className="rounded-full border border-line px-6 py-3 text-sm font-extrabold text-ink disabled:opacity-50"
          >
            Check again
          </button>
        )}
        <Link
          href={failure?.requiresLogin ? "/profile?mode=login" : "/profile"}
          className="rounded-full bg-blossomdeep px-6 py-3 text-sm font-extrabold text-white shadow-glow"
        >
          {failure?.requiresLogin ? "Sign in" : "View my orders"}
        </Link>
        <Link
          href="/"
          className="rounded-full border border-line px-6 py-3 text-sm font-extrabold text-stone"
        >
          Continue shopping
        </Link>
      </div>
    </section>
  );
}
