"use client";

import { useEffect, useState } from "react";
import {
  fallbackCatalogCategories,
  loadCatalogCategories,
} from "@/lib/catalog";
import { categoryName } from "@/lib/i18n";
import { useStore } from "@/lib/store";
import type { Category } from "@/lib/types";
import { CATEGORY_ICONS, RoseIcon } from "./icons";

/** Horizontally scrollable category circles, Flowwow-style but ours */
export default function CategoryRail() {
  const { category, setCategory, language } = useStore();
  const [categories, setCategories] = useState<Category[]>(fallbackCatalogCategories);

  useEffect(() => {
    let cancelled = false;
    loadCatalogCategories()
      .then((items) => {
        if (!cancelled && items.length > 0) setCategories(items);
      })
      .catch(() => {
        if (!cancelled) setCategories(fallbackCatalogCategories);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <nav aria-label="Categories" className="mx-auto max-w-7xl px-4 pt-8">
      <ul className="flex min-h-[7rem] gap-4 overflow-x-auto no-scrollbar px-1 pb-3 sm:gap-5 sm:justify-between">
        {categories.map((cat) => {
          const Icon = CATEGORY_ICONS[cat.id] ?? RoseIcon;
          const active = category === cat.id;
          return (
            <li key={cat.id} className="shrink-0 basis-[5.75rem] sm:basis-0 sm:flex-1">
              <button
                type="button"
                aria-pressed={active}
                aria-label={categoryName(language, cat.id)}
                onMouseDown={(event) => event.preventDefault()}
                onClick={() => {
                  setCategory(active ? null : cat.id);
                  document.getElementById("catalog")?.scrollIntoView({ behavior: "smooth" });
                }}
                className="group flex w-full flex-col items-center gap-1.5 rounded-2xl outline-none transition active:scale-[0.98]"
              >
                <span className="grid size-16 place-items-center rounded-full transition group-focus-visible:ring-2 group-focus-visible:ring-blossomdeep group-focus-visible:ring-offset-2 group-focus-visible:ring-offset-paper">
                  <span
                    className={`grid size-14 place-items-center rounded-full transition duration-300 group-hover:-translate-y-1 group-hover:shadow-soft group-active:scale-95 ${
                      active
                        ? "ring-2 ring-blossomdeep ring-offset-2 ring-offset-paper"
                        : "ring-0"
                    }`}
                    style={{ background: cat.tint }}
                  >
                    <span className="transition duration-300 group-hover:scale-110 group-hover:rotate-6">
                      <Icon />
                    </span>
                  </span>
                </span>
                <span
                  className={`flex min-h-[2.25rem] max-w-[5.75rem] items-start justify-center text-center text-xs font-semibold leading-tight transition-colors ${
                    active ? "text-blossomdeep" : "text-ink/80"
                  }`}
                >
                  {categoryName(language, cat.id)}
                </span>
              </button>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
