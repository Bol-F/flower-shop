"use client";

import { useState } from "react";
import type { Product } from "@/lib/types";
import BouquetArt from "./BouquetArt";

const badgeStyles: Record<string, string> = {
  discount: "bg-coral text-white",
  today: "bg-pine text-cream",
  lastone: "bg-lavender text-pinedeep",
};

export default function ProductCard({ product }: { product: Product }) {
  const [liked, setLiked] = useState(false);

  return (
    <article className="group relative flex flex-col overflow-hidden rounded-3xl bg-ivory shadow-card transition duration-300 hover:-translate-y-1.5 hover:shadow-petal">
      {/* image area */}
      <div
        className="relative aspect-[5/6] overflow-hidden"
        style={{ background: product.palette.backdrop }}
      >
        <BouquetArt
          palette={product.palette}
          className="absolute inset-x-0 bottom-0 mx-auto h-[92%] transition duration-500 group-hover:scale-[1.06]"
        />

        {/* badges */}
        <div className="absolute left-3 top-3 flex flex-col items-start gap-1.5">
          {product.badges.map((badge) => (
            <span
              key={badge.label}
              className={`rounded-full px-2.5 py-1 text-[11px] font-bold tracking-wide ${badgeStyles[badge.kind]}`}
            >
              {badge.label}
            </span>
          ))}
        </div>

        {/* favorite */}
        <button
          type="button"
          aria-label={liked ? "Remove from favorites" : "Add to favorites"}
          aria-pressed={liked}
          onClick={() => setLiked(!liked)}
          className="absolute right-3 top-3 grid size-9 place-items-center rounded-full bg-ivory/90 shadow-card backdrop-blur transition hover:scale-110 active:scale-95"
        >
          <svg
            viewBox="0 0 20 20"
            className={`size-4.5 transition ${liked ? "text-coral" : "text-fawn"}`}
            fill={liked ? "currentColor" : "none"}
            stroke="currentColor"
            strokeWidth="1.7"
          >
            <path d="M10 17 C4 12.5 2 9.5 2 6.8 C2 4.6 3.7 3 5.8 3 C7.3 3 8.9 3.8 10 5.6 C11.1 3.8 12.7 3 14.2 3 C16.3 3 18 4.6 18 6.8 C18 9.5 16 12.5 10 17 Z" strokeLinejoin="round" />
          </svg>
        </button>

        {/* quick buy — slides up on hover, always visible on touch layouts */}
        <button
          type="button"
          className="absolute inset-x-3 bottom-3 rounded-full bg-pine py-2.5 text-sm font-semibold text-cream opacity-100 transition duration-300 hover:bg-pinedeep lg:translate-y-14 lg:opacity-0 lg:group-hover:translate-y-0 lg:group-hover:opacity-100"
        >
          Buy now
        </button>
      </div>

      {/* info */}
      <div className="flex flex-1 flex-col gap-1 p-4">
        <div className="flex items-center gap-1 text-xs">
          <span className="text-coral">★</span>
          <span className="font-semibold">{product.rating.toFixed(1)}</span>
          <span className="text-fawn">({product.reviews})</span>
          <span className="mx-1 text-beige">•</span>
          <span className="truncate text-fawn">{product.shop}</span>
        </div>

        <h3 className="font-display text-lg font-semibold leading-snug text-pine">
          {product.name}
        </h3>

        <p className="mt-auto flex items-baseline gap-2 pt-1">
          <span className="text-xl font-bold text-ink">${product.price}</span>
          {product.oldPrice && (
            <span className="text-sm text-fawn line-through">${product.oldPrice}</span>
          )}
        </p>
      </div>
    </article>
  );
}
