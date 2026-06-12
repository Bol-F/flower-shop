"use client";

import { useState } from "react";

/** Stylized tulip mark — the Gulora logo */
function LogoMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" className={className} aria-hidden="true">
      <path
        d="M16 28 C16 20 16 16 16 13"
        stroke="#2e4639"
        strokeWidth="2.4"
        strokeLinecap="round"
        fill="none"
      />
      <path
        d="M9 6 C9 12 12 15 16 15 C20 15 23 12 23 6 C20.5 8.5 18.5 8.5 16 6 C13.5 8.5 11.5 8.5 9 6 Z"
        fill="#c96f7e"
      />
      <ellipse cx="11" cy="22" rx="4.5" ry="2" fill="#57755f" transform="rotate(-32 11 22)" />
      <ellipse cx="21" cy="24" rx="4.5" ry="2" fill="#57755f" transform="rotate(32 21 24)" />
    </svg>
  );
}

function SearchInput({ className }: { className?: string }) {
  return (
    <label className={`relative block ${className ?? ""}`}>
      <svg
        viewBox="0 0 20 20"
        className="absolute left-4 top-1/2 -translate-y-1/2 size-4 text-fawn"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        aria-hidden="true"
      >
        <circle cx="9" cy="9" r="6" />
        <path d="m14 14 4 4" strokeLinecap="round" />
      </svg>
      <input
        type="search"
        placeholder="Search bouquets, roses, gifts…"
        className="w-full rounded-full border border-beige bg-ivory py-2.5 pl-11 pr-4 text-sm outline-none placeholder:text-fawn focus:border-rose focus:ring-2 focus:ring-rose/20 transition"
      />
    </label>
  );
}

function PillSelect({ icon, label }: { icon: string; label: string }) {
  return (
    <button
      type="button"
      className="flex items-center gap-1.5 rounded-full border border-beige bg-ivory px-3.5 py-2 text-sm font-medium hover:border-rose hover:text-rosedeep transition whitespace-nowrap"
    >
      <span aria-hidden="true">{icon}</span>
      {label}
      <svg viewBox="0 0 10 6" className="size-2.5 text-fawn" fill="currentColor" aria-hidden="true">
        <path d="M0 0h10L5 6z" />
      </svg>
    </button>
  );
}

export default function Header() {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b border-beige/70 bg-ivory/85 backdrop-blur-md">
      <div className="mx-auto max-w-7xl px-4 py-3 flex items-center gap-4">
        {/* brand */}
        <a href="#" className="flex items-center gap-2 shrink-0">
          <LogoMark className="size-8" />
          <span className="font-display text-2xl font-semibold tracking-tight text-pine">
            Gulora
          </span>
        </a>

        <SearchInput className="hidden md:block flex-1 max-w-xl" />

        {/* desktop controls */}
        <div className="hidden lg:flex items-center gap-2 ml-auto">
          <PillSelect icon="📍" label="Tashkent" />
          <PillSelect icon="🕐" label="Today" />
          <PillSelect icon="💵" label="USD" />
        </div>

        {/* cart */}
        <button
          type="button"
          className="relative ml-auto lg:ml-2 flex items-center gap-2 rounded-full bg-pine px-4 py-2.5 text-sm font-semibold text-cream hover:bg-pinedeep transition shadow-card"
        >
          <svg viewBox="0 0 20 20" className="size-4" fill="none" stroke="currentColor" strokeWidth="1.7" aria-hidden="true">
            <path d="M3 4h2l2 10h8l2-7H6" strokeLinecap="round" strokeLinejoin="round" />
            <circle cx="8.5" cy="17" r="1.3" fill="currentColor" stroke="none" />
            <circle cx="14.5" cy="17" r="1.3" fill="currentColor" stroke="none" />
          </svg>
          <span className="hidden sm:inline">Cart</span>
          <span className="absolute -top-1.5 -right-1.5 grid size-5 place-items-center rounded-full bg-coral text-[10px] font-bold text-white">
            2
          </span>
        </button>

        {/* mobile hamburger */}
        <button
          type="button"
          onClick={() => setMenuOpen(!menuOpen)}
          aria-label="Open menu"
          className="md:hidden grid size-10 place-items-center rounded-full border border-beige bg-ivory"
        >
          {menuOpen ? (
            <svg viewBox="0 0 16 16" className="size-4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
              <path d="M3 3l10 10M13 3L3 13" />
            </svg>
          ) : (
            <svg viewBox="0 0 16 16" className="size-4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
              <path d="M2 4h12M2 8h12M2 12h12" />
            </svg>
          )}
        </button>
      </div>

      {/* mobile panel */}
      {menuOpen && (
        <div className="md:hidden border-t border-beige/70 bg-ivory px-4 py-4 space-y-3">
          <SearchInput />
          <div className="flex flex-wrap gap-2">
            <PillSelect icon="📍" label="Tashkent" />
            <PillSelect icon="🕐" label="Today" />
            <PillSelect icon="💵" label="USD" />
          </div>
        </div>
      )}
    </header>
  );
}
