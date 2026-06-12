import Link from "next/link";

export default function NotFound() {
  return (
    <main className="mx-auto grid max-w-7xl place-items-center px-4 py-24 text-center">
      <div>
        <p className="text-6xl">🥀</p>
        <h1 className="mt-4 font-display text-3xl font-bold sm:text-4xl">
          This page has wilted
        </h1>
        <p className="mt-2 text-sm text-stone">
          The bouquet you&apos;re looking for doesn&apos;t exist or was sold out.
        </p>
        <Link
          href="/"
          className="mt-6 inline-block rounded-full bg-blossomdeep px-8 py-3 text-sm font-bold text-white shadow-lift transition hover:bg-raspberry active:scale-95"
        >
          Back to the flowers
        </Link>
      </div>
    </main>
  );
}
