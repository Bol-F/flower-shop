"use client";

import { copy } from "@/lib/i18n";
import { useStore } from "@/lib/store";

export default function Hero() {
  const { language } = useStore();
  const t = copy[language].hero;
  const proofPoints =
    language === "RU"
      ? [
          ["Свежие цветы", "местные букеты"],
          ["Доставка", "выберите при заказе"],
          ["Удобная оплата", "доступные способы"],
        ]
      : language === "UZ"
        ? [
            ["Yangi gullar", "mahalliy guldastalar"],
            ["Yetkazib berish", "buyurtmada tanlang"],
            ["Qulay to‘lov", "mavjud usullar"],
          ]
        : [
            ["Fresh flowers", "browse local bouquets"],
            ["Delivery choices", "see options at checkout"],
            ["Payment choices", "see available methods"],
          ];

  return (
    <section className="relative overflow-hidden bg-gradient-to-br from-herowash via-rosewash to-paper">
      <div className="mx-auto flex max-w-[1180px] flex-col items-center justify-center px-5 py-10 text-center sm:py-12">
        <p className="w-full max-w-[330px] text-[11px] font-extrabold uppercase leading-6 tracking-[0.2em] text-blossomdeep sm:max-w-none sm:text-base sm:tracking-[0.34em]">
          {t.eyebrow}
        </p>

        <h1 className="mt-5 w-full max-w-full font-display text-[2.35rem] font-extrabold leading-[1.08] tracking-normal text-ink sm:text-6xl sm:leading-[1.05] lg:text-[4.5rem]">
          <span>{t.titleTop[0]}</span> <span>{t.titleTop[1]}</span>
          <span className="mt-2 block text-blossomdeep">
            <span>{t.titleAccent[0]}</span> <span>{t.titleAccent[1]}</span>
          </span>
        </h1>

        <p className="mt-5 w-full max-w-[330px] text-base leading-7 text-stone sm:max-w-[640px] sm:text-xl sm:leading-8">
          {t.text}
        </p>

        <div className="mt-6 grid w-full max-w-3xl grid-cols-3 gap-2 rounded-[1.75rem] border border-line bg-card/65 p-2 text-left shadow-soft backdrop-blur">
          {proofPoints.map(([value, label]) => (
            <div key={value} className="rounded-[1.25rem] bg-card px-2 py-3 sm:px-4">
              <p className="text-center text-xs font-extrabold text-ink sm:text-left sm:font-display sm:text-lg">
                {value}
              </p>
              <p className="mt-0.5 hidden text-[10px] font-bold uppercase tracking-[0.1em] text-stone sm:block">
                {label}
              </p>
            </div>
          ))}
        </div>

        <div className="mt-6 flex w-full max-w-[560px] flex-wrap justify-center gap-3">
          <a
            href="#catalog"
            className="rounded-full bg-raspberry px-6 py-3.5 text-sm font-extrabold text-white shadow-glow transition hover:-translate-y-1 hover:bg-berrydeep active:translate-y-0 sm:px-8 sm:text-base"
          >
            {t.primary}
          </a>
          <a
            href="#collections"
            className="rounded-full border-2 border-blossomdeep bg-card/70 px-6 py-3.5 text-sm font-extrabold text-blossomdeep transition hover:-translate-y-1 hover:bg-card hover:shadow-soft active:translate-y-0 sm:px-8 sm:text-base"
          >
            {t.secondary}
          </a>
        </div>
      </div>
    </section>
  );
}
