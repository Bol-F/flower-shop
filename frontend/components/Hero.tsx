"use client";

import { copy } from "@/lib/i18n";
import { useStore } from "@/lib/store";

export default function Hero() {
  const { language } = useStore();
  const t = copy[language].hero;
  const proofPoints = [
    ["60-180 min", "city delivery windows"],
    ["Test payments", "safe demo checkout"],
    ["Staff tools", "orders, stock, support"],
  ];

  return (
    <section className="relative overflow-hidden bg-gradient-to-br from-[#ffeaf4] via-[#fff2f8] to-white">
      <div className="mx-auto flex min-h-[calc(100vh-66px)] max-w-[1180px] flex-col items-center justify-center px-5 py-12 text-center sm:py-16">
        <p className="w-full max-w-[330px] text-[11px] font-extrabold uppercase leading-6 tracking-[0.2em] text-blossomdeep sm:max-w-none sm:text-base sm:tracking-[0.34em]">
          {t.eyebrow}
        </p>

        <h1 className="mt-9 w-full max-w-full font-display text-[2.35rem] font-extrabold leading-[1.08] tracking-normal text-ink sm:text-7xl sm:leading-[1.05] lg:text-[5.9rem]">
          <span className="block sm:inline">{t.titleTop[0]}</span>{" "}
          <span className="block sm:inline">{t.titleTop[1]}</span>
          <span className="mt-2 block text-blossomdeep">
            <span className="block sm:inline">{t.titleAccent[0]}</span>{" "}
            <span className="block sm:inline">{t.titleAccent[1]}</span>
          </span>
        </h1>

        <p className="mt-8 w-full max-w-[330px] text-base leading-7 text-stone sm:max-w-[640px] sm:text-2xl sm:leading-9">
          {t.text}
        </p>

        <div className="mt-10 grid w-full max-w-3xl gap-2 rounded-[1.75rem] border border-line bg-white/65 p-2 text-left shadow-soft backdrop-blur sm:grid-cols-3">
          {proofPoints.map(([value, label]) => (
            <div key={value} className="rounded-[1.25rem] bg-white px-4 py-3">
              <p className="font-display text-xl font-extrabold text-ink">
                {value}
              </p>
              <p className="mt-0.5 text-xs font-bold uppercase tracking-[0.12em] text-stone">
                {label}
              </p>
            </div>
          ))}
        </div>

        <div className="mt-8 flex w-[calc(100vw-2.5rem)] max-w-[560px] flex-col justify-center gap-4 sm:w-full sm:flex-row">
          <a
            href="#catalog"
            className="rounded-full bg-blossomdeep px-8 py-3.5 text-base font-extrabold text-white shadow-glow transition hover:-translate-y-1 hover:bg-raspberry active:translate-y-0"
          >
            {t.primary}
          </a>
          <a
            href="#catalog"
            className="rounded-full border-2 border-blossomdeep bg-white/70 px-8 py-3.5 text-base font-extrabold text-blossomdeep transition hover:-translate-y-1 hover:bg-white hover:shadow-soft active:translate-y-0"
          >
            {t.secondary}
          </a>
        </div>
      </div>
    </section>
  );
}
