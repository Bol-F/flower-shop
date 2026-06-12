import type { Metadata } from "next";
import AdminSupportInbox from "@/components/AdminSupportInbox";

export const metadata: Metadata = {
  title: "Admin support chat — Bloom & Petal",
  description: "Telegram-style support inbox for customer messages.",
};

export default function AdminPage() {
  return <AdminSupportInbox />;
}
