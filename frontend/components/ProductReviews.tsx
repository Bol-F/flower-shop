"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  deleteMyReview,
  fetchProductSocial,
  submitReview,
  type ProductSocial,
} from "@/lib/api";
import { copy } from "@/lib/i18n";
import { useStore } from "@/lib/store";
import { StarIcon } from "./icons";

/** How many comments to show before the "Show more" button. */
const COMMENTS_STEP = 5;

function dateLabel(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(new Date(value));
}

/** Read-only row of five stars. */
function Stars({ value, className }: { value: number; className: string }) {
  return (
    <span className="flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map((n) => (
        <StarIcon
          key={n}
          className={`${className} ${n <= value ? "text-blossom" : "text-stone/25"}`}
        />
      ))}
    </span>
  );
}

export default function ProductReviews({ productId }: { productId: string }) {
  const { user, language, showToast } = useStore();
  const t = copy[language].reviews;

  const [data, setData] = useState<ProductSocial | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [shown, setShown] = useState(COMMENTS_STEP);

  // review form
  const [rating, setRating] = useState(0);
  const [hover, setHover] = useState(0);
  const [body, setBody] = useState("");
  const [sending, setSending] = useState(false);

  // Load the summary; refetch when the signed-in user changes so the caller's
  // own review state comes through after hydration or sign-in. The review form
  // is seeded here so it opens in "edit" mode for an existing review.
  useEffect(() => {
    let cancelled = false;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoading(true);
    fetchProductSocial(productId)
      .then((d) => {
        if (cancelled) return;
        setData(d);
        setRating(d.my_review?.rating ?? 0);
        setBody(d.my_review?.body ?? "");
        setError("");
      })
      .catch(() => {
        if (!cancelled) setError(t.failed);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [productId, user?.id]);

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (rating < 1) {
      showToast(t.ratingRequired);
      return;
    }
    try {
      setSending(true);
      const res = await submitReview(productId, { rating, body: body.trim() });
      setData(res);
      setShown(COMMENTS_STEP);
      showToast(t.posted);
    } catch {
      showToast(t.failed);
    } finally {
      setSending(false);
    }
  }

  async function onDelete() {
    try {
      setSending(true);
      const res = await deleteMyReview(productId);
      setData(res);
      setRating(0);
      setBody("");
      showToast(t.deleted);
    } catch {
      showToast(t.failed);
    } finally {
      setSending(false);
    }
  }

  const average = data?.rating_average ?? 0;
  const ratingCount = data?.rating_count ?? 0;
  const reviews = data?.reviews ?? [];
  const editing = Boolean(data?.my_review);
  const activeStars = hover || rating;

  return (
    <section aria-label={t.title} className="mt-14">
      <h2 className="font-display text-2xl font-semibold sm:text-3xl">{t.title}</h2>

      <div className="mt-5 grid gap-6 lg:grid-cols-[300px_minmax(0,1fr)]">
        {/* ── rating summary + form ─────────────────────────────── */}
        <div className="space-y-4">
          {/* rating summary */}
          <div className="rounded-3xl bg-card p-6 shadow-soft">
            {ratingCount > 0 ? (
              <div className="text-center">
                <p className="font-display text-5xl font-extrabold leading-none">
                  {average.toFixed(1)}
                </p>
                <div className="mt-2 flex justify-center">
                  <Stars value={Math.round(average)} className="size-5" />
                </div>
                <p className="mt-1.5 text-sm text-stone">
                  {ratingCount} {t.count}
                </p>
              </div>
            ) : (
              <p className="py-2 text-center text-sm text-stone">
                {loading ? "…" : t.empty}
              </p>
            )}
          </div>

          {/* write / edit review, or sign-in prompt */}
          {user ? (
            <form onSubmit={onSubmit} className="rounded-3xl bg-card p-6 shadow-soft">
              <p className="font-display text-lg font-semibold">
                {editing ? t.editTitle : t.writeTitle}
              </p>

              <p className="mt-3 text-sm font-bold uppercase tracking-wider text-stone">
                {t.yourRating}
              </p>
              <div className="mt-1.5 flex gap-1" onMouseLeave={() => setHover(0)}>
                {[1, 2, 3, 4, 5].map((n) => (
                  <button
                    key={n}
                    type="button"
                    aria-label={`${n}`}
                    onClick={() => setRating(n)}
                    onMouseEnter={() => setHover(n)}
                    className="transition active:scale-90"
                  >
                    <StarIcon
                      className={`size-7 ${n <= activeStars ? "text-blossom" : "text-stone/25"}`}
                    />
                  </button>
                ))}
              </div>

              <textarea
                value={body}
                onChange={(e) => setBody(e.target.value)}
                rows={3}
                placeholder={t.placeholder}
                className="mt-4 w-full resize-none rounded-2xl border border-line bg-blush px-4 py-3 text-sm leading-relaxed outline-none transition placeholder:text-stone focus:border-blossomdeep focus:bg-white"
              />

              <div className="mt-3 flex items-center gap-3">
                <button
                  type="submit"
                  disabled={sending}
                  className="flex-1 rounded-full bg-blossomdeep px-6 py-3 text-sm font-bold text-white shadow-glow transition hover:bg-raspberry active:scale-95 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {editing ? t.update : t.submit}
                </button>
                {editing && (
                  <button
                    type="button"
                    onClick={onDelete}
                    disabled={sending}
                    className="rounded-full border border-line px-4 py-3 text-sm font-semibold text-stone transition hover:border-berry hover:text-berry active:scale-95 disabled:opacity-60"
                  >
                    {t.delete}
                  </button>
                )}
              </div>
            </form>
          ) : (
            <div className="rounded-3xl bg-card p-6 text-center shadow-soft">
              <p className="text-sm text-stone">{t.signIn}</p>
              <Link
                href="/profile?mode=login"
                className="mt-3 inline-flex rounded-full bg-blossomdeep px-6 py-2.5 text-sm font-bold text-white shadow-glow transition hover:bg-raspberry active:scale-95"
              >
                {t.signInCta}
              </Link>
            </div>
          )}
        </div>

        {/* ── comment list ──────────────────────────────────────── */}
        <div>
          {error ? (
            <div className="rounded-3xl bg-card p-8 text-center text-sm text-stone shadow-soft">
              {error}
            </div>
          ) : reviews.length === 0 ? (
            <div className="rounded-3xl bg-card p-8 text-center text-sm text-stone shadow-soft">
              {loading ? "…" : t.empty}
            </div>
          ) : (
            <ul className="space-y-3">
              {reviews.slice(0, shown).map((review) => (
                <li
                  key={review.id}
                  className="rounded-3xl bg-card p-5 shadow-soft"
                >
                  <div className="flex items-center gap-3">
                    <span className="grid size-10 shrink-0 place-items-center rounded-full bg-blush font-display font-bold text-raspberry">
                      {review.author.charAt(0).toUpperCase()}
                    </span>
                    <div className="min-w-0">
                      <p className="truncate text-sm font-bold">
                        {review.author}
                        {review.is_mine && (
                          <span className="ml-2 rounded-full bg-mint px-2 py-0.5 text-[11px] font-bold text-leaf">
                            ★
                          </span>
                        )}
                      </p>
                      <p className="text-xs text-stone">{dateLabel(review.created_at)}</p>
                    </div>
                    <span className="ml-auto">
                      <Stars value={review.rating} className="size-4" />
                    </span>
                  </div>
                  {review.body && (
                    <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-ink/80">
                      {review.body}
                    </p>
                  )}
                </li>
              ))}

              {reviews.length > shown && (
                <li className="flex justify-center pt-2">
                  <button
                    type="button"
                    onClick={() => setShown((s) => s + COMMENTS_STEP)}
                    className="rounded-full border border-line bg-card px-6 py-2.5 text-sm font-bold shadow-soft transition hover:border-blossom hover:text-raspberry active:scale-95"
                  >
                    {t.showMore} ({reviews.length - shown})
                  </button>
                </li>
              )}
            </ul>
          )}
        </div>
      </div>
    </section>
  );
}
