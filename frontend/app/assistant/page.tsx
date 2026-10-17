import type { Metadata } from "next";
import FlowerAssistant from "@/components/FlowerAssistant";

export const metadata: Metadata = {
  title: "Flower advice — Bloom & Petal",
  description: "Help choosing a bouquet and caring for your flowers.",
};

export default function AssistantPage() {
  return (
    <main>
      <FlowerAssistant />
    </main>
  );
}
