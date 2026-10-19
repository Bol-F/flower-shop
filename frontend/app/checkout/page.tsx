import type { Metadata } from "next";
import CheckoutClient from "@/components/CheckoutClient";
import "./checkout.css";

export const metadata: Metadata = {
  title: "Your bag & checkout — Bloom & Petal",
  description: "Review your flowers and choose delivery and payment options.",
};

export default function CheckoutPage() {
  return <CheckoutClient />;
}
