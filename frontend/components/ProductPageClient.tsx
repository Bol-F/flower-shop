"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  fallbackProduct,
  loadCatalogProduct,
} from "@/lib/catalog";
import type { Product } from "@/lib/types";
import ProductDetail from "./ProductDetail";

export default function ProductPageClient({ id }: { id: string }) {
  const [product, setProduct] = useState<Product | null>(() => fallbackProduct(id) ?? null);
  const [loading, setLoading] = useState(!fallbackProduct(id));
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    let cancelled = false;
    loadCatalogProduct(id)
      .then((item) => {
        if (cancelled) return;
        setProduct(item);
        setNotFound(false);
      })
      .catch(() => {
        if (cancelled) return;
        const fallback = fallbackProduct(id);
        setProduct(fallback ?? null);
        setNotFound(!fallback);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  if (product) return <ProductDetail product={product} />;

  return (
    <main className="mx-auto grid min-h-[calc(100vh-66px)] max-w-2xl place-items-center px-5 text-center">
      <section className="rounded-3xl bg-card px-8 py-12 shadow-soft">
        <p className="text-sm font-bold uppercase tracking-[0.18em] text-stone">
          {loading ? "Loading" : "Not found"}
        </p>
        <h1 className="mt-3 font-display text-3xl font-bold">
          {loading ? "Preparing bouquet details..." : "This product is unavailable"}
        </h1>
        {!loading && notFound && (
          <Link
            href="/#catalog"
            className="mt-6 inline-flex rounded-full bg-blossomdeep px-6 py-3 text-sm font-bold text-white shadow-glow"
          >
            Back to catalog
          </Link>
        )}
      </section>
    </main>
  );
}
