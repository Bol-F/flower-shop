"use client";

import Link from "next/link";
import { useState } from "react";
import type { Product } from "@/lib/types";
import { bouquetSizes, categories, products } from "@/lib/data";
import { formatPrice } from "@/lib/currency";
import { useStore } from "@/lib/store";
import BouquetArt from "./BouquetArt";
import ProductCard from "./ProductCard";
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
  const { currency, favorites, toggleFavorite, addToCart, showToast } = useStore();
  const [variant, setVariant] = useState(0);
  const [sizeId, setSizeId] = useState<"S" | "M" | "L">("M");
  const [qty, setQty] = useState(1);

  const liked = favorites.includes(product.id);
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
      <nav aria-label="Breadcrumb" className="text-sm text-stone">
        <ol className="flex flex-wrap items-center gap-1.5">
          <li>
            <Link href="/" className="transition hover:text-blossomdeep">
              Home
            </Link>
          </li>
          <li aria-hidden>/</li>
          <li>
            <Link href="/#catalog" className="transition hover:text-blossomdeep">
              {category?.name ?? "Catalog"}
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
            <BouquetArt
              key={variant}
              palette={product.palette}
              variant={variant}
              className="absolute inset-x-0 bottom-0 mx-auto h-[94%] animate-fade-up"
            />
            <div className="absolute left-4 top-4 flex flex-col items-start gap-1.5">
              {discount > 0 && (
                <span className="rounded-full bg-berry px-3 py-1.5 text-xs font-bold text-white">
                  −{discount}%
                </span>
              )}
              {product.isNew && (
                <span className="rounded-full bg-mint px-3 py-1.5 text-xs font-bold text-leaf">
                  New
                </span>
              )}
            </div>
            <button
              type="button"
              aria-label={liked ? "Remove from favorites" : "Add to favorites"}
              aria-pressed={liked}
              onClick={() => toggleFavorite(product.id)}
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
                aria-label={`View angle ${v + 1}`}
                aria-pressed={variant === v}
                onClick={() => setVariant(v)}
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
            <span className="text-stone">({product.reviews} reviews)</span>
            <span className="text-stone">·</span>
            <span className="font-semibold text-ink/80">{product.shop}</span>
          </div>

          <h1 className="mt-2 font-display text-3xl font-bold leading-tight sm:text-4xl">
            {product.name}
          </h1>

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
                −{discount}% today
              </span>
            )}
          </p>

          {/* delivery promise */}
          <div className="mt-4 flex flex-wrap gap-2">
            <span className="flex items-center gap-1.5 rounded-full bg-mint px-3.5 py-2 text-sm font-semibold text-leaf">
              <BoltIcon className="size-4" />
              {product.deliveryToday
                ? `Today in ~${product.deliveryMins} min`
                : "Tomorrow from 9:00"}
            </span>
            <span className="flex items-center gap-1.5 rounded-full bg-blush px-3.5 py-2 text-sm font-semibold text-raspberry">
              <CameraIcon className="size-4" />
              Photo before delivery
            </span>
            <span className="flex items-center gap-1.5 rounded-full bg-lilac px-3.5 py-2 text-sm font-semibold text-iris">
              <LeafIcon className="size-4" />
              Fresh guarantee
            </span>
          </div>

          {/* size picker */}
          {product.hasSizes && (
            <div className="mt-6">
              <p className="text-sm font-bold uppercase tracking-wider text-stone">
                Size
              </p>
              <div className="mt-2.5 flex gap-2.5">
                {bouquetSizes.map((s) => (
                  <button
                    key={s.id}
                    type="button"
                    aria-pressed={sizeId === s.id}
                    onClick={() => setSizeId(s.id)}
                    className={`flex-1 rounded-2xl border-2 px-4 py-3 text-left transition active:scale-[0.98] ${
                      sizeId === s.id
                        ? "border-blossomdeep bg-blush/60"
                        : "border-line bg-card hover:border-blossom"
                    }`}
                  >
                    <span className="block text-sm font-bold">
                      {s.id} · {s.label}
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
                aria-label="Decrease quantity"
                onClick={() => setQty(Math.max(1, qty - 1))}
                className="grid size-9 place-items-center rounded-full bg-blush text-raspberry transition hover:bg-blushdeep active:scale-90"
              >
                <MinusIcon className="size-4" />
              </button>
              <span className="w-8 text-center font-bold">{qty}</span>
              <button
                type="button"
                aria-label="Increase quantity"
                onClick={() => setQty(qty + 1)}
                className="grid size-9 place-items-center rounded-full bg-blush text-raspberry transition hover:bg-blushdeep active:scale-90"
              >
                <PlusIcon className="size-4" />
              </button>
            </div>

            <button
              type="button"
              onClick={() => {
                addToCart(product.id, qty);
                showToast(
                  qty === 1
                    ? `${product.name} added to cart`
                    : `${qty} × ${product.name} added to cart`,
                );
                setQty(1);
              }}
              className="flex-1 rounded-full bg-blossomdeep px-8 py-4 text-sm font-bold text-white shadow-lift transition hover:-translate-y-0.5 hover:bg-raspberry active:translate-y-0 sm:flex-none sm:px-12"
            >
              Add to cart — {formatPrice(unitPrice * qty, currency)}
            </button>
          </div>

          {/* description */}
          <div className="mt-8 rounded-3xl bg-card p-6 shadow-soft">
            <h2 className="font-display text-lg font-semibold">About this item</h2>
            <p className="mt-2 text-sm leading-relaxed text-ink/80">
              {product.description}
            </p>
            <h3 className="mt-5 text-sm font-bold uppercase tracking-wider text-stone">
              What&apos;s inside
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
              <p className="text-xs text-stone">
                Local florist studio · Tashkent · verified partner
              </p>
            </div>
            <span className="ml-auto flex shrink-0 items-center gap-1 text-sm font-bold">
              <StarIcon className="size-4 text-blossom" />
              {product.rating.toFixed(1)}
            </span>
          </div>
        </div>
      </div>

      {/* similar */}
      <section aria-label="You may also like" className="mt-14">
        <h2 className="font-display text-2xl font-semibold sm:text-3xl">
          You may also like
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
