"use client";

export default function ErrorPage({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="mx-auto grid max-w-7xl place-items-center px-4 py-24 text-center">
      <div>
        <p className="text-sm font-extrabold uppercase tracking-[0.18em] text-berry">
          Error
        </p>
        <h1 className="mt-4 font-display text-3xl font-bold sm:text-4xl">
          Something went wrong
        </h1>
        <p className="mt-2 text-sm text-stone">
          {error.message || "The page could not load. Please try again."}
        </p>
        <button
          type="button"
          onClick={reset}
          className="mt-6 rounded-full bg-blossomdeep px-8 py-3 text-sm font-bold text-white shadow-lift transition hover:bg-raspberry active:scale-95"
        >
          Try again
        </button>
      </div>
    </main>
  );
}
