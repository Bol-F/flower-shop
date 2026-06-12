"use client";

import { useMemo, useState } from "react";
import { products } from "@/lib/data";
import ProductCard from "./ProductCard";

type SortKey = "popular" | "price-asc" | "new" | "rated";

const sortOptions: Array<{ key: SortKey; label: string }> = [
  { key: "popular", label: "Popular" },
  { key: "price-asc", label: "Price low to high" },
  { key: "new", label: "New" },
  { key: "rated", label: "Best rated" },
];

/** chips that open real filter panels in a full app; decorative here */
const staticFilters = ["Price", "Flower type", "Occasion", "Color", "Rating"];

export default function Catalog() {
  const [sort, setSort] = useState<SortKey>("popular");
  const [todayOnly, setTodayOnly] = useState(false);

  const visible = useMemo(() => {
    const list = todayOnly ? products.filter((p) => p.deliveryToday) : [...products];
    switch (sort) {
      case "price-asc":
        return list.sort((a, b) => a.price - b.price);
      case "new":
        return list.sort((a, b) => Number(b.isNew) - Number(a.isNew));
      case "rated":
        return list.sort((a, b) => b.rating - a.rating);
      default:
        return list.sort((a, b) => b.popularity - a.popularity);
    }
  }, [sort, todayOnly]);

  return (
    <section id="catalog" className="mx-auto max-w-7xl px-4 py-16">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h2 className="font-display text-3xl sm:text-4xl font-semibold text-pine">
            Popular bouquets in Tashkent
          </h2>
          <p className="mt-2 text-fawn">
            {visible.length} bouquets from local florist studios
          </p>
        </div>

        {/* sort dropdown */}
        <label className="flex items-center gap-2 text-sm">
          <span className="text-fawn">Sort by</span>
          <select
            value={sort}
            onChange={(e) => setSort(e.target.value as SortKey)}
            className="rounded-full border border-beige bg-ivory px-4 py-2.5 font-medium outline-none focus:border-rose cursor-pointer"
          >
            {sortOptions.map((opt) => (
              <option key={opt.key} value={opt.key}>
                {opt.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      {/* filter chips */}
      <div className="mt-6 flex gap-2.5 overflow-x-auto no-scrollbar pb-1">
        <button
          type="button"
          onClick={() => setTodayOnly(!todayOnly)}
          aria-pressed={todayOnly}
          className={`shrink-0 rounded-full border px-4 py-2 text-sm font-medium transition ${
            todayOnly
              ? "border-coral bg-coral text-white"
              : "border-beige bg-ivory hover:border-coral hover:text-coraldeep"
          }`}
        >
          ⚡ Delivery today
        </button>
        {staticFilters.map((label) => (
          <button
            key={label}
            type="button"
            className="shrink-0 flex items-center gap-1.5 rounded-full border border-beige bg-ivory px-4 py-2 text-sm font-medium transition hover:border-rose hover:text-rosedeep"
          >
            {label}
            <svg viewBox="0 0 10 6" className="size-2.5 text-fawn" fill="currentColor" aria-hidden="true">
              <path d="M0 0h10L5 6z" />
            </svg>
          </button>
        ))}
      </div>

      {/* grid: 4 desktop / 2 tablet / 1 mobile */}
      <div className="mt-8 grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-5">
        {visible.map((product) => (
          <ProductCard key={product.id} product={product} />
        ))}
      </div>
    </section>
  );
}
