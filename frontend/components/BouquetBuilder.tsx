"use client";

import { useState } from "react";
import BouquetArt from "./BouquetArt";
import { palettes } from "@/lib/data";
import type { BouquetPalette } from "@/lib/types";

const flowerTypes = ["Roses", "Peonies", "Tulips", "Mixed"];

const colorChoices: Array<{ id: string; label: string; palette: BouquetPalette; swatch: string }> = [
  { id: "blush", label: "Blush pink", palette: palettes.pinkRose, swatch: "#e8a2ae" },
  { id: "coral", label: "Warm coral", palette: palettes.red, swatch: "#c9474f" },
  { id: "lavender", label: "Lavender", palette: palettes.lavender, swatch: "#b9a8d8" },
  { id: "ivory", label: "Ivory white", palette: palettes.white, swatch: "#f3ecdf" },
  { id: "sunny", label: "Sunny yellow", palette: palettes.tulip, swatch: "#f2b748" },
];

const budgets = [39, 59, 99, 149];

function OptionPill({
  selected,
  onClick,
  children,
}: {
  selected: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={selected}
      className={`rounded-full border px-4 py-2 text-sm font-medium transition ${
        selected
          ? "border-pine bg-pine text-cream"
          : "border-sand bg-ivory hover:border-pine/50"
      }`}
    >
      {children}
    </button>
  );
}

export default function BouquetBuilder() {
  const [flower, setFlower] = useState("Peonies");
  const [colorId, setColorId] = useState("blush");
  const [budget, setBudget] = useState(59);
  const [message, setMessage] = useState("");

  const chosen = colorChoices.find((c) => c.id === colorId) ?? colorChoices[0];

  return (
    <section id="builder" className="mx-auto max-w-7xl px-4 py-16">
      <div className="overflow-hidden rounded-[2.5rem] bg-beige/60 lg:grid lg:grid-cols-[1fr_minmax(300px,420px)]">
        {/* controls */}
        <div className="p-8 sm:p-12">
          <p className="text-xs font-semibold uppercase tracking-widest text-rosedeep">
            Bouquet atelier
          </p>
          <h2 className="mt-2 font-display text-3xl sm:text-4xl font-semibold text-pine">
            Build your own bouquet
          </h2>
          <p className="mt-3 max-w-md text-fawn">
            Pick the flowers, the mood and the budget — a florist composes it
            by hand and sends you a photo for approval.
          </p>

          <div className="mt-8 space-y-7">
            <fieldset>
              <legend className="mb-3 text-sm font-semibold text-ink">Flower type</legend>
              <div className="flex flex-wrap gap-2">
                {flowerTypes.map((type) => (
                  <OptionPill key={type} selected={flower === type} onClick={() => setFlower(type)}>
                    {type}
                  </OptionPill>
                ))}
              </div>
            </fieldset>

            <fieldset>
              <legend className="mb-3 text-sm font-semibold text-ink">Color palette</legend>
              <div className="flex flex-wrap items-center gap-3">
                {colorChoices.map((choice) => (
                  <button
                    key={choice.id}
                    type="button"
                    title={choice.label}
                    aria-pressed={colorId === choice.id}
                    onClick={() => setColorId(choice.id)}
                    className={`size-9 rounded-full border-4 transition hover:scale-110 ${
                      colorId === choice.id ? "border-pine" : "border-ivory shadow-card"
                    }`}
                    style={{ background: choice.swatch }}
                  />
                ))}
                <span className="text-sm text-fawn">{chosen.label}</span>
              </div>
            </fieldset>

            <fieldset>
              <legend className="mb-3 text-sm font-semibold text-ink">Budget</legend>
              <div className="flex flex-wrap gap-2">
                {budgets.map((value) => (
                  <OptionPill key={value} selected={budget === value} onClick={() => setBudget(value)}>
                    ${value}
                  </OptionPill>
                ))}
              </div>
            </fieldset>

            <label className="block">
              <span className="mb-3 block text-sm font-semibold text-ink">
                Message card <span className="font-normal text-fawn">(free)</span>
              </span>
              <input
                type="text"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                maxLength={120}
                placeholder="“Happy anniversary, my love…”"
                className="w-full max-w-md rounded-2xl border border-sand bg-ivory px-4 py-3 text-sm outline-none placeholder:text-fawn focus:border-rose focus:ring-2 focus:ring-rose/20"
              />
            </label>
          </div>

          <button
            type="button"
            className="mt-9 rounded-full bg-coral px-8 py-3.5 text-sm font-semibold text-white shadow-petal transition hover:bg-coraldeep hover:-translate-y-0.5"
          >
            Start designing — from ${budget}
          </button>
        </div>

        {/* live preview recolored by the chosen palette */}
        <div
          className="relative hidden lg:flex items-end justify-center transition-colors duration-500"
          style={{ background: chosen.palette.backdrop }}
        >
          <BouquetArt palette={chosen.palette} className="h-[85%] drop-shadow-xl" />
          <div className="absolute left-6 top-6 rounded-2xl bg-ivory/90 px-4 py-2.5 text-xs shadow-card backdrop-blur">
            <p className="font-semibold text-pine">{flower} · {chosen.label}</p>
            <p className="text-fawn">budget ${budget}{message && " · with card ✍️"}</p>
          </div>
        </div>
      </div>
    </section>
  );
}
