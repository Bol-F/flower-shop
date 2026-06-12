import type { Metadata } from "next";
import ProfileSettings from "@/components/ProfileSettings";

export const metadata: Metadata = {
  title: "Profile — Bloom & Petal",
  description: "Customer preferences and staff workspace for Bloom & Petal.",
};

export default async function ProfilePage({
  searchParams,
}: {
  searchParams?: Promise<{ mode?: string }>;
}) {
  const params = await searchParams;
  return <ProfileSettings initialMode={params?.mode === "login" ? "login" : "register"} />;
}
