import type { Metadata } from "next";
import { StoreProvider } from "@/lib/store";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import SupportChat from "@/components/SupportChat";
import "leaflet/dist/leaflet.css";
import "./globals.css";

export const metadata: Metadata = {
  title: "Bloom & Petal — Flower Delivery in Tashkent",
  description: "Fresh bouquets, gifts and romantic flowers delivered beautifully across Tashkent.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" data-scroll-behavior="smooth" className="h-full antialiased">
      <body className="flex min-h-full flex-col">
        <StoreProvider>
          <Header />
          <div className="flex-1">{children}</div>
          <Footer />
          <SupportChat />
        </StoreProvider>
      </body>
    </html>
  );
}
