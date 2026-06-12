"use client";

import { useMemo, useState } from "react";
import { categories, products } from "@/lib/data";
import { categoryName, copy } from "@/lib/i18n";
import { useStore } from "@/lib/store";
import ProductCard from "./ProductCard";
import { BoltIcon, CloseIcon } from "./icons";

type SortKey = "popular" | "price-asc" | "price-desc" | "new" | "rated";

const sortOptions: SortKey[] = ["popular", "price-asc", "price-desc", "new", "rated"];

export default function Catalog() {
  const { query, setQuery, category, setCategory, language } = useStore();
  const t = copy[language].catalog;
  const [sort, setSort] = useState<SortKey>("popular");
  const [todayOnly, setTodayOnly] = useState(false);
  const [saleOnly, setSaleOnly] = useState(false);

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase();
    const list = products.filter((p) => {
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
  }, [query, category, sort, todayOnly, saleOnly]);

  const activeCategory = categories.find((c) => c.id === category);
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
            {visible.length} {t.count}
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
      {visible.length > 0 ? (
        <div className="mt-7 grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-4">
          {visible.map((product) => (
            <ProductCard key={product.id} product={product} />
          ))}
        </div>
      ) : (
        <div className="mt-12 rounded-3xl bg-card py-16 text-center shadow-soft">
          <p className="text-4xl">🥀</p>
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
