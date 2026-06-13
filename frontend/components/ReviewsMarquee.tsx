"use client";

import { reviews } from "@/lib/data";
import { copy } from "@/lib/i18n";
import { useStore } from "@/lib/store";
import BouquetArt from "./BouquetArt";
import { StarIcon } from "./icons";

function ReviewCard({ review }: { review: (typeof reviews)[number] }) {
  return (
    <article className="flex w-80 shrink-0 flex-col rounded-3xl bg-card p-5 shadow-soft">
      <div className="flex items-center gap-3">
        <span
          className="grid size-11 shrink-0 place-items-center overflow-hidden rounded-full"
          style={{ background: review.palette.backdrop }}
        >
          <BouquetArt palette={review.palette} className="h-9" />
        </span>
        <div>
          <p className="text-sm font-bold">{review.name}</p>
          <p className="text-xs text-stone">
            {review.shop} · {review.date}
          </p>
        </div>
        <span className="ml-auto flex items-center gap-0.5">
          {Array.from({ length: review.rating }).map((_, i) => (
            <StarIcon key={i} className="size-3.5 text-blossom" />
          ))}
        </span>
      </div>
      <p className="mt-3 text-sm leading-relaxed text-ink/80">{review.text}</p>
    </article>
  );
}

/** Endless scrolling wall of love — pauses on hover */
export default function ReviewsMarquee() {
  const { language } = useStore();
  const t = copy[language].marquee;
  return (
    <section aria-label={t.label} className="overflow-hidden py-10">
      <div className="mx-auto max-w-7xl px-4">
        <h2 className="font-display text-3xl font-semibold sm:text-4xl">
          {t.title}
        </h2>
        <p className="mt-1.5 text-sm text-stone">
          {t.subtitle}
        </p>
      </div>

      <div className="relative mt-7">
        {/* edge fades */}
        <div className="pointer-events-none absolute inset-y-0 left-0 z-10 w-16 bg-gradient-to-r from-paper to-transparent" />
        <div className="pointer-events-none absolute inset-y-0 right-0 z-10 w-16 bg-gradient-to-l from-paper to-transparent" />

        <div className="marquee-track flex w-max animate-marquee gap-4 pl-4">
          {[...reviews, ...reviews].map((review, i) => (
            <ReviewCard key={`${review.id}-${i}`} review={review} />
          ))}
        </div>
      </div>
    </section>
  );
}
