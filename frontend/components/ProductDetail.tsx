"use client";

/* eslint-disable @next/next/no-img-element */
import Link from "next/link";
import { useState } from "react";
import type { Product } from "@/lib/types";
import { bouquetSizes, categories, products } from "@/lib/data";
import { formatPrice } from "@/lib/currency";
import { categoryName, copy } from "@/lib/i18n";
import { useStore } from "@/lib/store";
import BouquetArt from "./BouquetArt";
import ProductCard from "./ProductCard";
import ProductReviews from "./ProductReviews";
import {
  BoltIcon,
  CameraIcon,
  HeartIcon,
  LeafIcon,
  MinusIcon,
  PlusIcon,
  StarIcon,
} from "./icons";

export default function ProductDetail({ product }: { product: Product }) {
  const { currency, language, favorites, toggleFavorite, addToCart, showToast } =
    useStore();
  const t = copy[language].detail;
  const [sizeId, setSizeId] = useState<"S" | "M" | "L">("M");
  // The 3 gallery shots map 1:1 to the S / M / L sizes, so choosing one keeps
  // the other in sync. bouquetSizes is the single source for that ordering.
  const [variant, setVariant] = useState(() =>
    product.hasSizes ? bouquetSizes.findIndex((s) => s.id === "M") : 0,
  );
  const [qty, setQty] = useState(1);

  const chooseSize = (id: "S" | "M" | "L") => {
    setSizeId(id);
    setVariant(bouquetSizes.findIndex((s) => s.id === id));
  };
  const chooseVariant = (v: number) => {
    setVariant(v);
    if (product.hasSizes) setSizeId(bouquetSizes[v].id);
  };

  const liked = favorites.includes(product.id);
  const purchasable = product.isAvailable !== false && product.isInStock !== false;
  const category = categories.find((c) => c.id === product.category);
  const size = bouquetSizes.find((s) => s.id === sizeId)!;
  const unitPrice = product.hasSizes
    ? Math.round(product.price * size.multiplier)
    : product.price;
  const discount = product.oldPrice
    ? Math.round((1 - product.price / product.oldPrice) * 100)
    : 0;

  const similar = products
    .filter((p) => p.id !== product.id)
    .sort(
      (a, b) =>
        Number(b.category === product.category) -
          Number(a.category === product.category) ||
        b.popularity - a.popularity,
    )
    .slice(0, 4);

  return (
    <main className="mx-auto max-w-7xl px-4 py-8">
      {/* breadcrumbs */}
      <nav aria-label={t.breadcrumb} className="text-sm text-stone">
        <ol className="flex flex-wrap items-center gap-1.5">
          <li>
            <Link href="/" className="transition hover:text-blossomdeep">
              {t.home}
            </Link>
          </li>
          <li aria-hidden>/</li>
          <li>
            <Link href="/#catalog" className="transition hover:text-blossomdeep">
              {category ? categoryName(language, category.id) : t.catalog}
            </Link>
          </li>
          <li aria-hidden>/</li>
          <li className="font-semibold text-ink/80">{product.name}</li>
        </ol>
      </nav>

      <div className="mt-6 grid gap-8 lg:grid-cols-2">
        {/* gallery */}
        <div>
          <div
            className="relative aspect-[5/6] overflow-hidden rounded-[2rem] shadow-soft sm:aspect-[4/5] lg:aspect-square"
            style={{ background: product.palette.backdrop }}
          >
            {product.image ? (
              <img
                src={product.image}
                alt={product.name}
                className="absolute inset-0 h-full w-full object-cover animate-fade-up"
              />
            ) : (
              <BouquetArt
                key={variant}
                palette={product.palette}
                variant={variant}
                className="absolute inset-x-0 bottom-0 mx-auto h-[94%] animate-fade-up"
              />
            )}
            <div className="absolute left-4 top-4 flex flex-col items-start gap-1.5">
              {discount > 0 && (
                <span className="rounded-full bg-berry px-3 py-1.5 text-xs font-bold text-white">
                  Save {discount}%
                </span>
              )}
              {product.isNew && (
                <span className="rounded-full bg-mint px-3 py-1.5 text-xs font-bold text-leaf">
                  {copy[language].product.new}
                </span>
              )}
            </div>
            <button
              type="button"
              aria-label={liked ? t.favoriteRemove : t.favoriteAdd}
              aria-pressed={liked}
              onClick={() => toggleFavorite(product)}
              className="absolute right-4 top-4 grid size-11 place-items-center rounded-full bg-card/90 shadow-soft backdrop-blur transition hover:scale-110 active:scale-90"
            >
              <HeartIcon
                filled={liked}
                className={`size-5 ${liked ? "animate-pop text-berry" : "text-stone"}`}
              />
            </button>
          </div>

          {/* thumbnails — different shots of the bouquet */}
          <div className="mt-3 flex gap-3">
            {[0, 1, 2].map((v) => (
              <button
                key={v}
                type="button"
                aria-label={
                  product.hasSizes
                    ? `${t.size} ${bouquetSizes[v].id} / ${t.sizes[bouquetSizes[v].id]}`
                    : `${t.angle} ${v + 1}`
                }
                aria-pressed={variant === v}
                onClick={() => chooseVariant(v)}
                className={`grid h-20 w-20 place-items-center overflow-hidden rounded-2xl transition hover:-translate-y-0.5 ${
                  variant === v
                    ? "ring-2 ring-blossomdeep ring-offset-2 ring-offset-paper"
                    : "opacity-70 hover:opacity-100"
                }`}
                style={{ background: product.palette.backdrop }}
              >
                <BouquetArt palette={product.palette} variant={v} className="h-16" />
              </button>
            ))}
          </div>
        </div>

        {/* info column */}
        <div>
          <div className="flex items-center gap-2 text-sm">
            <StarIcon className="size-4 text-blossom" />
            <span className="font-bold">{product.rating.toFixed(1)}</span>
            <span className="text-stone">({product.reviews} {t.reviews})</span>
            <span className="text-stone">/</span>
            <span className="font-semibold text-ink/80">{product.shop}</span>
          </div>

          <h1 className="mt-2 font-display text-3xl font-bold leading-tight sm:text-4xl">
            {product.name}
          </h1>

          {product.source === "mock" && (
            <div className="mt-4 rounded-2xl border border-[#f5d79c] bg-[#fff8e7] px-4 py-3 text-sm font-semibold text-[#8a5a0a]">
              Demo catalog item. Start the Django backend and run
              <span className="font-extrabold"> python manage.py seed_demo </span>
              to test live product data.
            </div>
          )}

          <p className="mt-3 flex items-baseline gap-3">
            <span className="text-3xl font-extrabold tracking-tight">
              {formatPrice(unitPrice * qty, currency)}
            </span>
            {product.oldPrice && qty === 1 && !product.hasSizes && (
              <span className="text-lg font-semibold text-stone line-through">
                {formatPrice(product.oldPrice, currency)}
              </span>
            )}
            {product.oldPrice && (product.hasSizes || qty > 1) && (
              <span className="rounded-full bg-berrysoft px-2.5 py-1 text-xs font-bold text-berry">
                Save {discount}% {t.discountToday}
              </span>
            )}
          </p>

          {/* delivery promise */}
          <div className="mt-4 flex flex-wrap gap-2">
            <span className="flex items-center gap-1.5 rounded-full bg-mint px-3.5 py-2 text-sm font-semibold text-leaf">
              <BoltIcon className="size-4" />
              {product.deliveryToday
                ? t.deliveryToday.replace("{min}", String(product.deliveryMins))
                : t.deliveryTomorrow}
            </span>
            <span className="flex items-center gap-1.5 rounded-full bg-blush px-3.5 py-2 text-sm font-semibold text-raspberry">
              <CameraIcon className="size-4" />
              {t.photo}
            </span>
            <span className="flex items-center gap-1.5 rounded-full bg-lilac px-3.5 py-2 text-sm font-semibold text-iris">
              <LeafIcon className="size-4" />
              {t.fresh}
            </span>
          </div>

          {/* size picker */}
          {product.hasSizes && (
            <div className="mt-6">
              <p className="text-sm font-bold uppercase tracking-wider text-stone">
                {t.size}
              </p>
              <div className="mt-2.5 flex gap-2.5">
                {bouquetSizes.map((s) => (
                  <button
                    key={s.id}
                    type="button"
                    aria-pressed={sizeId === s.id}
                    onClick={() => chooseSize(s.id)}
                    className={`flex-1 rounded-2xl border-2 px-4 py-3 text-left transition active:scale-[0.98] ${
                      sizeId === s.id
                        ? "border-blossomdeep bg-blush/60"
                        : "border-line bg-card hover:border-blossom"
                    }`}
                  >
                    <span className="block text-sm font-bold">
                      {s.id} / {t.sizes[s.id]}
                    </span>
                    <span className="mt-0.5 block text-sm font-semibold text-blossomdeep">
                      {formatPrice(Math.round(product.price * s.multiplier), currency)}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* qty + add to cart */}
          <div className="mt-6 flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-1 rounded-full border border-line bg-card p-1.5">
              <button
                type="button"
                aria-label={t.qtyDecrease}
                onClick={() => setQty(Math.max(1, qty - 1))}
                className="grid size-9 place-items-center rounded-full bg-blush text-raspberry transition hover:bg-blushdeep active:scale-90"
              >
                <MinusIcon className="size-4" />
              </button>
              <span className="w-8 text-center font-bold">{qty}</span>
              <button
                type="button"
                aria-label={t.qtyIncrease}
                onClick={() => setQty(qty + 1)}
                className="grid size-9 place-items-center rounded-full bg-blush text-raspberry transition hover:bg-blushdeep active:scale-90"
              >
                <PlusIcon className="size-4" />
              </button>
            </div>

            <button
              type="button"
              disabled={!purchasable}
              onClick={() => {
                addToCart(product, qty);
                showToast(
                  qty === 1
                    ? t.addedOne.replace("{name}", product.name)
                    : t.addedMany
                        .replace("{qty}", String(qty))
                        .replace("{name}", product.name),
                );
                setQty(1);
              }}
              className="flex-1 rounded-full bg-blossomdeep px-8 py-4 text-sm font-bold text-white shadow-lift transition hover:-translate-y-0.5 hover:bg-raspberry active:translate-y-0 disabled:cursor-not-allowed disabled:bg-ink/20 disabled:text-stone disabled:shadow-none sm:flex-none sm:px-12"
            >
              {purchasable ? t.addToCart : "Out of stock"} -{" "}
              {formatPrice(unitPrice * qty, currency)}
            </button>
          </div>

          <div className="mt-4 grid gap-2 rounded-3xl border border-line bg-card p-4 text-sm shadow-soft sm:grid-cols-3">
            <div>
              <p className="text-xs font-extrabold uppercase tracking-wider text-stone">
                Availability
              </p>
              <p className="mt-1 font-bold text-ink">
                {purchasable ? "Ready to order" : "Out of stock"}
              </p>
            </div>
            <div>
              <p className="text-xs font-extrabold uppercase tracking-wider text-stone">
                Stock
              </p>
              <p className="mt-1 font-bold text-ink">
                {typeof product.stock === "number"
                  ? `${product.stock} available`
                  : "Live stock"}
              </p>
            </div>
            <div>
              <p className="text-xs font-extrabold uppercase tracking-wider text-stone">
                Checkout
              </p>
              <p className="mt-1 font-bold text-ink">
                Cash, card, or online test payment
              </p>
            </div>
          </div>

          {/* description */}
          <div className="mt-8 rounded-3xl bg-card p-6 shadow-soft">
            <h2 className="font-display text-lg font-semibold">{t.about}</h2>
            <p className="mt-2 text-sm leading-relaxed text-ink/80">
              {product.description}
            </p>
            <h3 className="mt-5 text-sm font-bold uppercase tracking-wider text-stone">
              {t.inside}
            </h3>
            <ul className="mt-2.5 flex flex-wrap gap-2">
              {product.composition.map((item) => (
                <li
                  key={item}
                  className="rounded-full bg-paper px-3.5 py-1.5 text-sm font-medium text-ink/80"
                >
                  {item}
                </li>
              ))}
            </ul>
          </div>

          {/* shop card */}
          <div className="mt-4 flex items-center gap-4 rounded-3xl bg-card p-5 shadow-soft">
            <span className="grid size-12 shrink-0 place-items-center rounded-2xl bg-blush font-display text-lg font-bold text-raspberry">
              {product.shop.charAt(0)}
            </span>
            <div className="min-w-0">
              <p className="truncate font-bold">{product.shop}</p>
              <p className="text-xs text-stone">{t.shopMeta}</p>
            </div>
            <span className="ml-auto flex shrink-0 items-center gap-1 text-sm font-bold">
              <StarIcon className="size-4 text-blossom" />
              {product.rating.toFixed(1)}
            </span>
          </div>
        </div>
      </div>

      {/* reviews, ratings & likes */}
      <ProductReviews productId={product.id} />

      {/* similar */}
      <section aria-label={t.similar} className="mt-14">
        <h2 className="font-display text-2xl font-semibold sm:text-3xl">
          {t.similar}
        </h2>
        <div className="mt-5 grid grid-cols-2 gap-4 md:grid-cols-4">
          {similar.map((p) => (
            <ProductCard key={p.id} product={p} />
          ))}
        </div>
      </section>
    </main>
  );
}
