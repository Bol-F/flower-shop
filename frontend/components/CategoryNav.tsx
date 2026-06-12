"use client";

import { useState } from "react";
import { categories } from "@/lib/data";

export default function CategoryNav() {
  const [active, setActive] = useState("roses");

  return (
    <nav aria-label="Categories" className="mx-auto max-w-7xl px-4">
      <ul className="flex gap-3 overflow-x-auto no-scrollbar py-2">
        {categories.map((cat) => {
          const isActive = cat.id === active;
          return (
            <li key={cat.id} className="shrink-0">
              <button
                type="button"
                onClick={() => setActive(cat.id)}
                className={`group flex items-center gap-2.5 rounded-2xl border px-4 py-2.5 text-sm font-medium transition
                  ${
                    isActive
                      ? "border-pine bg-pine text-cream shadow-card"
                      : "border-beige bg-ivory text-ink hover:border-rose hover:-translate-y-0.5"
                  }`}
              >
                <span
                  className={`grid size-8 place-items-center rounded-xl text-base transition group-hover:scale-110 ${
                    isActive ? "bg-cream/15" : cat.tint
                  }`}
                  aria-hidden="true"
                >
                  {cat.emoji}
                </span>
                {cat.name}
              </button>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
