"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { deleteMyReview, fetchProductSocial, submitReview, type ProductSocial } from "@/lib/api";
import { copy } from "@/lib/i18n";
import { useStore } from "@/lib/store";
import { StarIcon } from "./icons";
import "./catalog-product.css";

const COMMENTS_STEP = 5;
const headings = { EN: "Customer reviews", RU: "Отзывы покупателей", UZ: "Xaridorlar sharhlari" };

function dateLabel(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(new Date(value));
}

function Stars({ value }: { value: number }) {
  return (
    <span className="flower-review-stars" aria-label={`${value} / 5`}>
      {[1, 2, 3, 4, 5].map((n) => (
        <StarIcon
          key={n}
          className={`size-4 ${n <= value ? "flower-star-active" : "flower-star-empty"}`}
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
  const [rating, setRating] = useState(0);
  const [hover, setHover] = useState(0);
  const [body, setBody] = useState("");
  const [sending, setSending] = useState(false);

  useEffect(() => {
    let cancelled = false;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoading(true);
    fetchProductSocial(productId)
      .then((result) => {
        if (cancelled) return;
        setData(result);
        setRating(result.my_review?.rating ?? 0);
        setBody(result.my_review?.body ?? "");
        setShown(COMMENTS_STEP);
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
      const result = await submitReview(productId, { rating, body: body.trim() });
      setData(result);
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
      const result = await deleteMyReview(productId);
      setData(result);
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
    <section aria-labelledby="customer-reviews-title" className="flower-reviews">
      <h2 id="customer-reviews-title" className="flower-section-heading">
        {headings[language]}
      </h2>
      <div className="flower-reviews-grid">
        <div>
          <div className="flower-review-summary" aria-live="polite">
            {loading ? (
              "…"
            ) : error ? null : ratingCount > 0 ? (
              <>
                <p className="flower-review-average">{average.toFixed(1)}</p>
                <Stars value={Math.round(average)} />
                <p>
                  {ratingCount} {t.count}
                </p>
              </>
            ) : (
              <p>{t.empty}</p>
            )}
          </div>

          {user ? (
            <form onSubmit={onSubmit} className="flower-review-form">
              <h3>{editing ? t.editTitle : t.writeTitle}</h3>
              <p id="review-rating-label" className="ui-label">
                {t.yourRating}
              </p>
              <div
                className="flower-review-rating"
                role="group"
                aria-labelledby="review-rating-label"
                onMouseLeave={() => setHover(0)}
              >
                {[1, 2, 3, 4, 5].map((n) => (
                  <button
                    key={n}
                    type="button"
                    aria-label={`${n}`}
                    aria-pressed={rating === n}
                    onClick={() => setRating(n)}
                    onMouseEnter={() => setHover(n)}
                  >
                    <StarIcon
                      className={`size-6 ${n <= activeStars ? "flower-star-active" : "flower-star-empty"}`}
                    />
                  </button>
                ))}
              </div>
              <textarea
                value={body}
                onChange={(event) => setBody(event.target.value)}
                rows={3}
                aria-label={t.placeholder}
                placeholder={t.placeholder}
                className="ui-field"
              />
              <div className="flower-review-actions">
                <button type="submit" disabled={sending} className="ui-button">
                  {editing ? t.update : t.submit}
                </button>
                {editing && (
                  <button
                    type="button"
                    onClick={() => void onDelete()}
                    disabled={sending}
                    className="ui-button-secondary"
                  >
                    {t.delete}
                  </button>
                )}
              </div>
            </form>
          ) : (
            <div className="flower-review-state">
              <p>{t.signIn}</p>
              <Link href="/profile?mode=login" className="flower-review-signin">
                {t.signInCta}
              </Link>
            </div>
          )}
        </div>

        <div>
          {error ? (
            <p role="alert" className="flower-review-state flower-review-error">
              {error}
            </p>
          ) : reviews.length > 0 ? (
            <>
              <ul className="flower-review-list">
                {reviews.slice(0, shown).map((review) => (
                  <li key={review.id}>
                    <div className="flower-review-row">
                      <div>
                        <p className="flower-review-author">
                          {review.author}
                          {review.is_mine && (
                            <span className="flower-review-own">{t.editTitle}</span>
                          )}
                        </p>
                        <p className="flower-review-date">{dateLabel(review.created_at)}</p>
                      </div>
                      <Stars value={review.rating} />
                    </div>
                    {review.body && <p className="flower-review-body">{review.body}</p>}
                  </li>
                ))}
              </ul>
              {reviews.length > shown && (
                <button
                  type="button"
                  onClick={() => setShown((current) => current + COMMENTS_STEP)}
                  className="flower-load-more"
                >
                  {t.showMore} ({reviews.length - shown})
                </button>
              )}
            </>
          ) : null}
        </div>
      </div>
    </section>
  );
}
