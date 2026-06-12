import { reviews } from "@/lib/data";
import BouquetArt from "./BouquetArt";

function Stars({ count }: { count: number }) {
  return (
    <span className="text-coral text-sm tracking-tight" aria-label={`${count} out of 5 stars`}>
      {"★".repeat(count)}
      <span className="text-beige">{"★".repeat(5 - count)}</span>
    </span>
  );
}

export default function Reviews() {
  return (
    <section className="bg-blush/50 py-16">
      <div className="mx-auto max-w-7xl px-4">
        <h2 className="font-display text-3xl sm:text-4xl font-semibold text-pine text-center">
          Loved across Tashkent
        </h2>
        <p className="mt-2 text-center text-fawn">
          4.9 average from 12,000+ verified orders
        </p>

        <div className="mt-10 grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
          {reviews.map((review) => (
            <figure
              key={review.id}
              className="flex flex-col rounded-3xl bg-ivory p-6 shadow-card"
            >
              <div className="flex items-center justify-between">
                <Stars count={review.rating} />
                <div
                  className="size-12 rounded-2xl p-1"
                  style={{ background: review.palette.backdrop }}
                >
                  <BouquetArt palette={review.palette} className="h-full w-full" />
                </div>
              </div>
              <blockquote className="mt-4 flex-1 text-sm leading-relaxed text-ink/80">
                “{review.text}”
              </blockquote>
              <figcaption className="mt-5 border-t border-beige pt-4 text-xs">
                <p className="font-semibold text-pine">{review.name}</p>
                <p className="mt-0.5 text-fawn">
                  {review.date} · ordered from {review.shop}
                </p>
              </figcaption>
            </figure>
          ))}
        </div>
      </div>
    </section>
  );
}
