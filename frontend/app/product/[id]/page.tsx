import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { products } from "@/lib/data";
import ProductDetail from "@/components/ProductDetail";

interface Props {
  params: Promise<{ id: string }>;
}

export function generateStaticParams() {
  return products.map((p) => ({ id: p.id }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;
  const product = products.find((p) => p.id === id);
  if (!product) return { title: "Not found — Gulora" };
  return {
    title: `${product.name} — Gulora`,
    description: product.description,
  };
}

export default async function ProductPage({ params }: Props) {
  const { id } = await params;
  const product = products.find((p) => p.id === id);
  if (!product) notFound();

  return <ProductDetail product={product} />;
}
