import type { Metadata } from "next";
import { fallbackCatalogProducts } from "@/lib/catalog";
import ProductPageClient from "@/components/ProductPageClient";

interface Props {
  params: Promise<{ id: string }>;
}

export function generateStaticParams() {
  return fallbackCatalogProducts.map((p) => ({ id: p.id }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;
  const product = fallbackCatalogProducts.find((p) => p.id === id);
  if (!product) return { title: "Not found - Bloom & Petal" };
  return {
    title: `${product.name} - Bloom & Petal`,
    description: product.description,
  };
}

export default async function ProductPage({ params }: Props) {
  const { id } = await params;
  return <ProductPageClient id={id} />;
}
