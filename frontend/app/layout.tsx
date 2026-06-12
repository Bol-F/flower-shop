import type { Metadata } from "next";
import { Manrope, Playfair_Display } from "next/font/google";
import { StoreProvider } from "@/lib/store";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import SupportChat from "@/components/SupportChat";
import "./globals.css";

const playfair = Playfair_Display({
  variable: "--font-playfair",
  subsets: ["latin", "cyrillic"],
  weight: ["600", "700", "800"],
});

const manrope = Manrope({
  variable: "--font-manrope",
  subsets: ["latin", "cyrillic"],
});

export const metadata: Metadata = {
  title: "Bloom & Petal — Flower Delivery in Tashkent",
  description:
    "Fresh bouquets, gifts and romantic flowers delivered beautifully across Tashkent.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="ru"
      className={`${playfair.variable} ${manrope.variable} h-full antialiased`}
    >
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
