"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { copy } from "@/lib/i18n";
import { useStore } from "@/lib/store";

export default function Footer() {
  const pathname = usePathname();
  const { language } = useStore();
  const t = copy[language].footer;
  const columns = [t.columns.catalog, t.columns.occasions, t.columns.clients];

  // Staff work in the admin dashboard — the marketing footer is just noise there.
  if (pathname?.startsWith("/admin")) return null;

  return (
    <footer className="mt-10 border-t border-line bg-gradient-to-br from-[#fff2f8] via-[#fde7f1] to-[#fbdaeb]">
      <div className="mx-auto grid max-w-7xl gap-10 px-4 py-12 sm:grid-cols-2 lg:grid-cols-5">
        {/* brand */}
        <div className="lg:col-span-2">
          <Link href="/" className="flex items-center gap-2.5">
            <span className="text-3xl leading-none">🌸</span>
            <span className="font-display text-2xl font-bold text-blossomdeep">
              Bloom &amp; Petal
            </span>
          </Link>
          <p className="mt-3 max-w-xs text-sm leading-relaxed text-stone">
            {t.tagline}
          </p>
          <p className="mt-4 text-sm font-semibold">
            {t.hours}
            <br />
            <a href="tel:+998711234567" className="text-blossomdeep hover:underline">
              +998 71 123-45-67
            </a>
          </p>
        </div>

        {columns.map((col) => (
          <nav key={col.title} aria-label={col.title}>
            <p className="text-sm font-bold uppercase tracking-wider text-stone">
              {col.title}
            </p>
            <ul className="mt-3 flex flex-col gap-2">
              {col.links.map((link) => (
                <li key={link}>
                  <a
                    href="#catalog"
                    className="text-sm text-ink/75 transition hover:text-blossomdeep"
                  >
                    {link}
                  </a>
                </li>
              ))}
            </ul>
          </nav>
        ))}
      </div>

      <div className="border-t border-line">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-2 px-4 py-5 text-xs text-stone">
          <p>{t.copyright}</p>
          <p>
            {t.currencyPre}
            <Link href="/profile" className="font-semibold text-blossomdeep hover:underline">
              {t.currencyLink}
            </Link>
            {t.currencyPost}
          </p>
        </div>
      </div>
    </footer>
  );
}
