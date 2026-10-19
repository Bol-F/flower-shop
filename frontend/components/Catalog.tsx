"use client";

import { useEffect, useMemo, useState } from "react";
import { fetchCities, type ApiCity } from "@/lib/api";
import {
  fallbackCatalogCategories,
  fallbackCatalogProducts,
  loadCatalogCategories,
  loadCatalogProducts,
} from "@/lib/catalog";
import { copy } from "@/lib/i18n";
import { useStore } from "@/lib/store";
import type { Category, Product } from "@/lib/types";
import ProductCard from "./ProductCard";
import { CloseIcon, SearchIcon } from "./icons";
import "./catalog-product.css";

type SortKey = "popular" | "price-asc" | "price-desc" | "new" | "rated";
const sortOptions: SortKey[] = ["popular", "price-asc", "price-desc", "new", "rated"];
const PAGE_SIZE = 8;
const labels = {
  EN: {
    title: "Find your bouquet",
    search: "Search flowers",
    city: "Delivery city",
    sort: "Sort",
    more: "Load more flowers",
    offline:
      "The shop is temporarily unreachable. Showing the demo catalog; live availability and checkout require a connection.",
    loading: "Loading flowers",
    found: "flowers found",
    clear: "Clear search",
  },
  RU: {
    title: "Найдите свой букет",
    search: "Поиск цветов",
    city: "Город доставки",
    sort: "Сортировка",
    more: "Показать ещё цветы",
    offline:
      "Магазин временно недоступен. Показан демонстрационный каталог; для проверки наличия и оформления нужно подключение.",
    loading: "Загрузка цветов",
    found: "букетов найдено",
    clear: "Очистить поиск",
  },
  UZ: {
    title: "Guldastangizni toping",
    search: "Gullarni qidirish",
    city: "Yetkazish shahri",
    sort: "Saralash",
    more: "Yana gullarni ko‘rish",
    offline:
      "Do‘kon bilan aloqa vaqtincha yo‘q. Namoyish katalogi ko‘rsatilmoqda; mavjudlik va buyurtma uchun ulanish kerak.",
    loading: "Gullar yuklanmoqda",
    found: "guldasta topildi",
    clear: "Qidiruvni tozalash",
  },
};

function cityToSlug(city: string) {
  return city
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

export default function Catalog() {
  const { query, setQuery, category, setCategory, language, city, setCity } = useStore();
  const t = copy[language].catalog;
  const text = labels[language];
  const [allProducts, setAllProducts] = useState<Product[]>(fallbackCatalogProducts);
  const [allCategories, setAllCategories] = useState<Category[]>(fallbackCatalogCategories);
  const [cities, setCities] = useState<ApiCity[]>([]);
  const [loading, setLoading] = useState(true);
  const [usingFallback, setUsingFallback] = useState(false);
  const [sort, setSort] = useState<SortKey>("popular");
  const [todayOnly, setTodayOnly] = useState(false);
  const [saleOnly, setSaleOnly] = useState(false);
  const [shown, setShown] = useState(PAGE_SIZE);

  useEffect(() => {
    let cancelled = false;
    void fetchCities().then(
      (items) => {
        if (!cancelled) setCities(items);
      },
      () => {
        if (!cancelled) setCities([]);
      },
    );
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      try {
        const [products, categories] = await Promise.all([
          loadCatalogProducts(cityToSlug(city)),
          loadCatalogCategories(),
        ]);
        if (cancelled) return;
        // A live empty response must stay empty, never become demo inventory.
        setAllProducts(products);
        setAllCategories(categories);
        setUsingFallback(false);
      } catch {
        if (cancelled) return;
        setAllProducts(fallbackCatalogProducts);
        setAllCategories(fallbackCatalogCategories);
        setUsingFallback(true);
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
      return !q || `${p.name} ${p.shop} ${p.category}`.toLowerCase().includes(q);
    });
    switch (sort) {
      case "price-asc":
        return list.sort((a, b) => a.price - b.price);
      case "price-desc":
        return list.sort((a, b) => b.price - a.price);
      case "new":
        return list.sort((a, b) => Number(b.isNew) - Number(a.isNew));
      case "rated":
        return list.sort((a, b) => (b.rating ?? 0) - (a.rating ?? 0));
      default:
        return list.sort((a, b) => b.popularity - a.popularity);
    }
  }, [allProducts, query, category, sort, todayOnly, saleOnly]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setShown(PAGE_SIZE);
  }, [query, category, sort, todayOnly, saleOnly, city]);

  const activeCategory = allCategories.find((item) => item.id === category);
  const activeCategoryName = activeCategory
    ? ((copy[language].categories as Record<string, string>)[activeCategory.id] ??
      activeCategory.name)
    : null;
  const cityNames = [...new Set([city, ...cities.map((item) => item.name)])];
  const shownProducts = visible.slice(0, shown);
  const remaining = visible.length - shownProducts.length;
  const hasTodayFilter = allProducts.some((product) => product.deliveryToday === true);
  const hasSaleFilter = allProducts.some((product) => product.oldPrice !== undefined);

  return (
    <section id="catalog" className="site-container flower-catalog" aria-labelledby="catalog-title">
      <div className="flower-catalog-toolbar">
        <h2 id="catalog-title" className="flower-section-heading">
          {text.title}
        </h2>
        <div className="flower-catalog-controls">
          <label className="flower-search">
            <span className="sr-only">{text.search}</span>
            <SearchIcon />
            <input
              id="catalog-search"
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder={text.search}
              className="ui-field"
            />
          </label>
          <select
            aria-label={text.city}
            value={city}
            onChange={(event) => setCity(event.target.value)}
            className="ui-field flower-select"
          >
            {cityNames.map((name) => (
              <option key={name} value={name}>
                {text.city}: {name}
              </option>
            ))}
          </select>
          <select
            aria-label={text.sort}
            value={sort}
            onChange={(event) => setSort(event.target.value as SortKey)}
            className="ui-field flower-select"
          >
            {sortOptions.map((option) => (
              <option key={option} value={option}>
                {text.sort}: {t.sortOptions[option]}
              </option>
            ))}
          </select>
        </div>
      </div>

      <p role="status" className="sr-only">
        {loading ? text.loading : `${visible.length} ${text.found}`}
      </p>
      {usingFallback && <p className="flower-notice">{text.offline}</p>}

      {(hasTodayFilter || hasSaleFilter || activeCategory || query.trim()) && (
        <div className="flower-catalog-filters">
          {hasTodayFilter && (
            <button
              type="button"
              onClick={() => setTodayOnly(!todayOnly)}
              aria-pressed={todayOnly}
              className="flower-filter"
            >
              {t.today}
            </button>
          )}
          {hasSaleFilter && (
            <button
              type="button"
              onClick={() => setSaleOnly(!saleOnly)}
              aria-pressed={saleOnly}
              className="flower-filter"
            >
              {t.sale}
            </button>
          )}
          {activeCategory && (
            <button type="button" onClick={() => setCategory(null)} className="flower-filter">
              {activeCategoryName}
              <CloseIcon />
            </button>
          )}
          {query.trim() && (
            <button
              type="button"
              onClick={() => setQuery("")}
              aria-label={text.clear}
              className="flower-filter"
            >
              “{query.trim()}”<CloseIcon />
            </button>
          )}
        </div>
      )}

      {loading ? (
        <div className="flower-grid" aria-hidden="true">
          {Array.from({ length: 4 }, (_, index) => (
            <div key={index}>
              <div className="flower-skeleton-photo" />
              <div className="flower-skeleton-line" />
              <div className="flower-skeleton-line" />
            </div>
          ))}
        </div>
      ) : visible.length > 0 ? (
        <>
          <div className="flower-grid">
            {shownProducts.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
          {remaining > 0 && (
            <button
              type="button"
              onClick={() => setShown((current) => current + PAGE_SIZE)}
              className="flower-load-more"
            >
              {text.more} ({remaining})
            </button>
          )}
        </>
      ) : (
        <div className="flower-empty">
          <h3>{t.emptyTitle}</h3>
          <p>{t.emptyText}</p>
          <button
            type="button"
            onClick={() => {
              setQuery("");
              setCategory(null);
              setTodayOnly(false);
              setSaleOnly(false);
            }}
            className="ui-button-secondary"
          >
            {t.clear}
          </button>
        </div>
      )}
    </section>
  );
}
