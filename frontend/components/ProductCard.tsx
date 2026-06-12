"use client";

import Link from "next/link";
import type { Product } from "@/lib/types";
import { formatPrice } from "@/lib/currency";
import { copy } from "@/lib/i18n";
import { useStore } from "@/lib/store";
import BouquetArt from "./BouquetArt";
import { BoltIcon, HeartIcon, PlusIcon, StarIcon } from "./icons";

export default function ProductCard({ product }: { product: Product }) {
  const { currency, language, favorites, toggleFavorite, addToCart, showToast } =
    useStore();
  const t = copy[language].product;
  const liked = favorites.includes(product.id);
  const discount = product.oldPrice
    ? Math.round((1 - product.price / product.oldPrice) * 100)
    : 0;

  return (
    <article className="group relative flex flex-col rounded-3xl bg-card p-2 shadow-soft transition duration-300 hover:-translate-y-1 hover:shadow-lift">
      {/* image area */}
      <div
        className="relative aspect-[4/5] overflow-hidden rounded-2xl"
        style={{ background: product.palette.backdrop }}
      >
        <BouquetArt
          palette={product.palette}
          className="absolute inset-x-0 bottom-0 mx-auto h-[94%] transition duration-500 group-hover:scale-[1.07] group-hover:-rotate-1"
        />

        {/* badges */}
        <div className="absolute left-2.5 top-2.5 z-20 flex flex-col items-start gap-1.5">
          {discount > 0 && (
            <span className="rounded-full bg-berry px-2.5 py-1 text-[11px] font-bold text-white">
              −{discount}%
            </span>
          )}
          {product.isNew && (
            <span className="rounded-full bg-mint px-2.5 py-1 text-[11px] font-bold text-leaf">
              {t.new}
            </span>
          )}
        </div>

        {/* favorite */}
        <button
          type="button"
          aria-label={liked ? "Remove from favorites" : "Add to favorites"}
          aria-pressed={liked}
          onClick={() => toggleFavorite(product.id)}
          className="absolute right-2.5 top-2.5 z-20 grid size-9 place-items-center rounded-full bg-card/90 shadow-soft backdrop-blur transition hover:scale-110 active:scale-90"
        >
          <HeartIcon
            filled={liked}
            className={`size-4.5 transition ${liked ? "animate-pop text-berry" : "text-stone"}`}
          />
        </button>

        {/* quick add */}
        <button
          type="button"
          aria-label={`Add ${product.name} to cart`}
          onClick={() => {
            addToCart(product.id);
            showToast(`${product.name} added to cart`);
          }}
          className="absolute bottom-2.5 right-2.5 z-20 grid size-10 place-items-center rounded-full bg-card text-blossomdeep shadow-soft transition hover:bg-blossomdeep hover:text-white hover:shadow-lift active:scale-90"
        >
          <PlusIcon className="size-5" />
        </button>
      </div>

      {/* info — price first, marketplace style */}
      <div className="flex flex-1 flex-col gap-0.5 px-2 pb-2 pt-2.5">
        <p className="flex items-baseline gap-2">
          <span className="text-lg font-extrabold tracking-tight">
            {formatPrice(product.price, currency)}
          </span>
          {product.oldPrice && (
            <span className="text-xs font-semibold text-stone line-through">
              {formatPrice(product.oldPrice, currency)}
            </span>
          )}
        </p>

        <h3 className="line-clamp-2 text-sm font-medium leading-snug text-ink/90">
          {product.name}
        </h3>

        <div className="mt-1.5 flex items-center gap-1 text-xs text-stone">
          <StarIcon className="size-3.5 text-blossom" />
          <span className="font-bold text-ink/80">{product.rating.toFixed(1)}</span>
          <span>({product.reviews})</span>
          <span className="mx-0.5">·</span>
          {product.deliveryToday ? (
            <span className="flex items-center gap-0.5 font-semibold text-leaf">
              <BoltIcon className="size-3" />
              {product.deliveryMins} min
            </span>
          ) : (
            <span className="font-semibold">{t.tomorrow}</span>
          )}
        </div>
      </div>

      {/* stretched link below the action buttons */}
      <Link
        href={`/product/${product.id}`}
        aria-label={`View ${product.name}`}
        className="absolute inset-0 z-10 rounded-3xl"
      />
    </article>
  );
}
