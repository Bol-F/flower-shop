"use client";

import { useEffect, useMemo, useState } from "react";
import {
  fallbackCatalogCategories,
  fallbackCatalogProducts,
  loadCatalogCategories,
  loadCatalogProducts,
} from "@/lib/catalog";
import { categoryName, copy } from "@/lib/i18n";
import { useStore } from "@/lib/store";
import type { Category, Product } from "@/lib/types";
import ProductCard from "./ProductCard";
import { BoltIcon, CloseIcon } from "./icons";

type SortKey = "popular" | "price-asc" | "price-desc" | "new" | "rated";

const sortOptions: SortKey[] = ["popular", "price-asc", "price-desc", "new", "rated"];

/** Cards shown before "Show more" — two rows on the widest (4-col) grid. */
const PAGE_SIZE = 8;

function cityToSlug(city: string) {
  return city
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

export default function Catalog() {
  const { query, setQuery, category, setCategory, language, city } = useStore();
  const t = copy[language].catalog;
  const [allProducts, setAllProducts] = useState<Product[]>(fallbackCatalogProducts);
  const [allCategories, setAllCategories] = useState<Category[]>(
    fallbackCatalogCategories,
  );
  const [loading, setLoading] = useState(true);
  const [usingFallback, setUsingFallback] = useState(false);
  const [catalogError, setCatalogError] = useState("");
  const [sort, setSort] = useState<SortKey>("popular");
  const [todayOnly, setTodayOnly] = useState(false);
  const [saleOnly, setSaleOnly] = useState(false);
  const [shown, setShown] = useState(PAGE_SIZE);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [products, categories] = await Promise.all([
          loadCatalogProducts(cityToSlug(city)),
          loadCatalogCategories(),
        ]);
        if (cancelled) return;
        setAllProducts(products.length > 0 ? products : fallbackCatalogProducts);
        setAllCategories(categories.length > 0 ? categories : fallbackCatalogCategories);
        setUsingFallback(false);
        setCatalogError("");
      } catch {
        if (cancelled) return;
        setAllProducts(fallbackCatalogProducts);
        setAllCategories(fallbackCatalogCategories);
        setUsingFallback(true);
        setCatalogError(
          "Live backend is offline or unreachable. Showing bundled demo flowers.",
        );
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, [city]);

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase();
    const list = allProducts.filter((p) => {
      if (todayOnly && !p.deliveryToday) return false;
      if (saleOnly && !p.oldPrice) return false;
      if (category && p.category !== category) return false;
      if (q && !`${p.name} ${p.shop} ${p.category}`.toLowerCase().includes(q)) return false;
      return true;
    });
    switch (sort) {
      case "price-asc":
        return list.sort((a, b) => a.price - b.price);
      case "price-desc":
        return list.sort((a, b) => b.price - a.price);
      case "new":
        return list.sort((a, b) => Number(b.isNew) - Number(a.isNew));
      case "rated":
        return list.sort((a, b) => b.rating - a.rating);
      default:
        return list.sort((a, b) => b.popularity - a.popularity);
    }
  }, [allProducts, query, category, sort, todayOnly, saleOnly]);

  // A fresh filter/search/sort starts the list back at two rows.
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setShown(PAGE_SIZE);
  }, [query, category, sort, todayOnly, saleOnly]);

  const shownProducts = visible.slice(0, shown);
  const remaining = visible.length - shownProducts.length;

  const activeCategory = allCategories.find((c) => c.id === category);
  const activeCategoryName = activeCategory
    ? categoryName(language, activeCategory.id)
    : null;

  return (
    <section id="catalog" className="mx-auto max-w-7xl scroll-mt-24 px-4 py-12">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h2 className="font-display text-3xl font-semibold sm:text-4xl">
            {activeCategoryName ?? t.title}
          </h2>
          <p className="mt-1.5 text-sm text-stone">
            {loading ? "..." : visible.length} {t.count}
            {usingFallback && (
              <span className="ml-2 font-semibold text-raspberry">
                Demo catalog
              </span>
            )}
          </p>
        </div>

        {/* sort dropdown */}
        <label className="flex items-center gap-2 text-sm">
          <span className="text-stone">{t.sort}</span>
          <select
            value={sort}
            onChange={(e) => setSort(e.target.value as SortKey)}
            className="cursor-pointer rounded-full border border-line bg-card px-4 py-2.5 font-semibold shadow-soft outline-none transition focus:border-blossom"
          >
            {sortOptions.map((opt) => (
              <option key={opt} value={opt}>
                {t.sortOptions[opt]}
              </option>
            ))}
          </select>
        </label>
      </div>

      {(usingFallback || catalogError) && (
        <div className="mt-5 rounded-3xl border border-[#f5d79c] bg-[#fff8e7] px-4 py-3 text-sm font-semibold text-[#8a5a0a] shadow-soft">
          {catalogError || "Showing demo catalog data."} Checkout and account
          features need the Django API.
        </div>
      )}

      {/* filter chips */}
      <div className="mt-5 flex gap-2.5 overflow-x-auto no-scrollbar pb-1">
        <button
          type="button"
          onClick={() => setTodayOnly(!todayOnly)}
          aria-pressed={todayOnly}
          className={`flex shrink-0 items-center gap-1.5 rounded-full border px-4 py-2 text-sm font-semibold transition active:scale-95 ${
            todayOnly
              ? "border-leaf bg-leaf text-white"
              : "border-line bg-card hover:border-leaf hover:text-leaf"
          }`}
        >
          <BoltIcon className="size-3.5" />
          {t.today}
        </button>
        <button
          type="button"
          onClick={() => setSaleOnly(!saleOnly)}
          aria-pressed={saleOnly}
          className={`shrink-0 rounded-full border px-4 py-2 text-sm font-semibold transition active:scale-95 ${
            saleOnly
              ? "border-berry bg-berry text-white"
              : "border-line bg-card hover:border-berry hover:text-berry"
          }`}
        >
          {t.sale}
        </button>

        {/* active filters echoed as removable chips */}
        {activeCategory && (
          <button
            type="button"
            onClick={() => setCategory(null)}
            className="flex shrink-0 items-center gap-1.5 rounded-full bg-blush px-4 py-2 text-sm font-semibold text-raspberry transition hover:bg-blushdeep active:scale-95"
          >
            {activeCategoryName}
            <CloseIcon className="size-3.5" />
          </button>
        )}
        {query.trim() && (
          <button
            type="button"
            onClick={() => setQuery("")}
            className="flex shrink-0 items-center gap-1.5 rounded-full bg-blush px-4 py-2 text-sm font-semibold text-raspberry transition hover:bg-blushdeep active:scale-95"
          >
            “{query.trim()}”
            <CloseIcon className="size-3.5" />
          </button>
        )}
      </div>

      {/* grid */}
      {loading ? (
        <div className="mt-7 grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-4">
          {Array.from({ length: 4 }).map((_, index) => (
            <div
              key={index}
              className="min-h-[22rem] animate-pulse rounded-3xl bg-card p-2 shadow-soft"
            >
              <div className="aspect-[4/5] rounded-2xl bg-blush" />
              <div className="mx-2 mt-3 h-4 rounded-full bg-line" />
              <div className="mx-2 mt-2 h-4 w-2/3 rounded-full bg-line" />
            </div>
          ))}
        </div>
      ) : visible.length > 0 ? (
        <>
          <div className="mt-7 grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-4">
            {shownProducts.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>

          {remaining > 0 && (
            <div className="mt-8 flex justify-center">
              <button
                type="button"
                onClick={() => setShown((s) => s + PAGE_SIZE)}
                className="rounded-full border border-line bg-card px-7 py-3 text-sm font-bold shadow-soft transition hover:border-blossom hover:text-raspberry active:scale-95"
              >
                {t.showMore} ({remaining})
              </button>
            </div>
          )}
        </>
      ) : (
        <div className="mt-12 rounded-3xl border border-line bg-card px-5 py-16 text-center shadow-soft">
          <p className="mx-auto grid size-14 place-items-center rounded-2xl bg-blush text-2xl font-extrabold text-blossomdeep">
            0
          </p>
          <p className="mt-3 font-display text-xl font-semibold">
            {t.emptyTitle}
          </p>
          <p className="mt-1 text-sm text-stone">
            {t.emptyText}
          </p>
          <button
            type="button"
            onClick={() => {
              setQuery("");
              setCategory(null);
              setTodayOnly(false);
              setSaleOnly(false);
            }}
            className="mt-5 rounded-full bg-blossomdeep px-6 py-2.5 text-sm font-bold text-white transition hover:bg-raspberry active:scale-95"
          >
            {t.clear}
          </button>
        </div>
      )}
    </section>
  );
}
