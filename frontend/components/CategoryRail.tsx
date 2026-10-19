"use client";

import { useEffect, useState } from "react";
import { fallbackCatalogCategories, loadCatalogCategories } from "@/lib/catalog";
import { copy } from "@/lib/i18n";
import { useStore } from "@/lib/store";
import type { Category } from "@/lib/types";
import "./catalog-product.css";

const labels = {
  EN: { title: "Made for every occasion", all: "All flowers", nav: "Flower categories" },
  RU: { title: "Для каждого повода", all: "Все цветы", nav: "Категории цветов" },
  UZ: { title: "Har bir lahza uchun", all: "Barcha gullar", nav: "Gul toifalari" },
};

export default function CategoryRail() {
  const { category, setCategory, language } = useStore();
  const [categories, setCategories] = useState<Category[]>(fallbackCatalogCategories);
  const t = labels[language];

  useEffect(() => {
    let cancelled = false;
    loadCatalogCategories()
      .then((items) => {
        if (!cancelled) setCategories(items);
      })
      .catch(() => {
        if (!cancelled) setCategories(fallbackCatalogCategories);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  function chooseCategory(id: string | null) {
    setCategory(id);
    document.getElementById("catalog")?.scrollIntoView({ behavior: "smooth" });
  }

  return (
    <section id="collections" className="site-container occasion-section">
      <h2 className="occasion-heading">{t.title}</h2>
      <nav aria-label={t.nav} className="occasion-navigation">
        <button
          type="button"
          aria-pressed={category === null}
          onClick={() => chooseCategory(null)}
          className="occasion-link"
        >
          {t.all}
        </button>
        {categories.map((item) => (
          <button
            key={item.id}
            type="button"
            aria-pressed={category === item.id}
            onClick={() => chooseCategory(category === item.id ? null : item.id)}
            className="occasion-link"
          >
            {(copy[language].categories as Record<string, string>)[item.id] ?? item.name}
          </button>
        ))}
      </nav>
    </section>
  );
}
