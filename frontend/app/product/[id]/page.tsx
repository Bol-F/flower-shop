import type { Metadata } from "next";
import { cache } from "react";
import { connection } from "next/server";
import { fallbackProduct, loadCatalogProduct } from "@/lib/catalog";
import ProductPageClient from "@/components/ProductPageClient";

interface Props {
  params: Promise<{ id: string }>;
}

const getProduct = cache(async (id: string) => {
  // Inventory and prices must be read at request time, never frozen at build.
  await connection();
  try {
    return await loadCatalogProduct(id);
  } catch {
    return fallbackProduct(id) ?? null;
  }
});

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;
  const product = await getProduct(id);
  if (!product) return { title: "Not found - Bloom & Petal" };
  return {
    title: `${product.name} - Bloom & Petal`,
    description: product.description,
  };
}

export default async function ProductPage({ params }: Props) {
  const { id } = await params;
  const product = await getProduct(id);
  return <ProductPageClient id={id} initialProduct={product} />;
}
