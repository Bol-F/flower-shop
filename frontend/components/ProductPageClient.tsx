"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ApiError } from "@/lib/api";
import { fallbackProduct, loadCatalogProduct } from "@/lib/catalog";
import type { Product } from "@/lib/types";
import ProductDetail from "./ProductDetail";
import "./catalog-product.css";

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
          <p role="status" className="site-container flower-notice">
            We couldn’t refresh this bouquet. Checkout will confirm the latest price and
            availability.
          </p>
        )}
        <ProductDetail product={product} />
      </>
    );

  return (
    <main className="site-container flower-product-state">
      <p className="ui-label">{loading ? "Loading" : "Not found"}</p>
      <h1 className="flower-section-heading">
        {loading ? "Preparing bouquet details..." : "This product is unavailable"}
      </h1>
      {!loading && notFound && (
        <Link href="/#catalog" className="ui-button">
          Back to catalog
        </Link>
      )}
    </main>
  );
}
