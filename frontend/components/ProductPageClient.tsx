"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ApiError } from "@/lib/api";
import { fallbackProduct, loadCatalogProduct } from "@/lib/catalog";
import type { Product } from "@/lib/types";
import ProductDetail from "./ProductDetail";

export default function ProductPageClient({
  id,
  initialProduct,
}: {
  id: string;
  initialProduct: Product | null;
}) {
  const [product, setProduct] = useState<Product | null>(initialProduct);
  const [loading, setLoading] = useState(!initialProduct);
  const [notFound, setNotFound] = useState(false);
  const [refreshFailed, setRefreshFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    let generation = 0;
    const refresh = () => {
      const current = ++generation;
      return loadCatalogProduct(id)
        .then((item) => {
          if (cancelled || current !== generation) return;
          setProduct(item);
          setNotFound(false);
          setRefreshFailed(false);
        })
        .catch((error: unknown) => {
          if (cancelled || current !== generation) return;
          if (initialProduct?.source === "api") {
            if (error instanceof ApiError && error.status === 404) {
              setProduct(null);
              setNotFound(true);
            } else setRefreshFailed(true);
            return;
          }
          const fallback = fallbackProduct(id);
          setProduct(fallback ?? null);
          setNotFound(!fallback);
        })
        .finally(() => {
          if (!cancelled && current === generation) setLoading(false);
        });
    };
    void refresh();
    const onFocus = () => {
      void refresh();
    };
    window.addEventListener("focus", onFocus);
    return () => {
      cancelled = true;
      window.removeEventListener("focus", onFocus);
    };
  }, [id, initialProduct]);

  if (product)
    return (
      <>
        {refreshFailed && (
          <p role="status" className="mx-auto max-w-7xl bg-blush px-5 py-3 text-sm text-stone">
            We couldn’t refresh this bouquet. Checkout will confirm the latest price and
            availability.
          </p>
        )}
        <ProductDetail product={product} />
      </>
    );

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
