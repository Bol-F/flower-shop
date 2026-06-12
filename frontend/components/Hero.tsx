import BouquetArt from "./BouquetArt";
import { palettes } from "@/lib/data";

function Petal({ className, color }: { className?: string; color: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} aria-hidden="true">
      <path
        d="M12 2 C18 6 20 13 12 22 C4 13 6 6 12 2 Z"
        fill={color}
        opacity="0.55"
      />
    </svg>
  );
}

export default function Hero() {
  return (
    <section className="relative overflow-hidden">
      {/* drifting decorative petals */}
      <Petal className="absolute left-[6%] top-12 size-8 animate-float" color="#efcdc6" />
      <Petal className="absolute left-[42%] top-6 size-5 animate-float-slow" color="#b9a8d8" />
      <Petal className="absolute right-[8%] bottom-10 size-7 animate-float" color="#e8a2ae" />

      <div className="mx-auto max-w-7xl px-4 py-14 lg:py-20 grid lg:grid-cols-2 items-center gap-12">
        {/* copy */}
        <div>
          <p className="inline-flex items-center gap-2 rounded-full bg-blush px-4 py-1.5 text-xs font-semibold tracking-wide text-rosedeep uppercase">
            🌷 Tashkent flower marketplace
          </p>
          <h1 className="mt-5 font-display text-5xl sm:text-6xl lg:text-7xl font-semibold leading-[1.04] text-pine">
            Fresh flowers,{" "}
            <em className="text-rose not-italic font-light italic">delivered</em>{" "}
            beautifully
          </h1>
          <p className="mt-6 max-w-md text-lg text-fawn leading-relaxed">
            Same-day bouquets, gift boxes and plants from the city&apos;s best
            local florists — with a photo of your order before it leaves the
            studio.
          </p>

          <div className="mt-8 flex flex-wrap gap-3">
            <a
              href="#catalog"
              className="rounded-full bg-coral px-7 py-3.5 text-sm font-semibold text-white shadow-petal hover:bg-coraldeep hover:-translate-y-0.5 transition"
            >
              Shop bouquets
            </a>
            <a
              href="#builder"
              className="rounded-full border-2 border-pine/15 bg-ivory px-7 py-3.5 text-sm font-semibold text-pine hover:border-pine/40 hover:-translate-y-0.5 transition"
            >
              Create custom bouquet
            </a>
          </div>

          <dl className="mt-10 flex gap-8 text-sm">
            {[
              ["4.9★", "average rating"],
              ["30 min", "fastest delivery"],
              ["120+", "local florists"],
            ].map(([value, label]) => (
              <div key={label}>
                <dt className="font-display text-2xl font-semibold text-pine">{value}</dt>
                <dd className="text-fawn">{label}</dd>
              </div>
            ))}
          </dl>
        </div>

        {/* visual */}
        <div className="relative mx-auto w-full max-w-md lg:max-w-none">
          <div
            className="relative mx-auto aspect-[4/5] max-w-sm rounded-[44%_56%_52%_48%/55%_44%_56%_45%] shadow-petal"
            style={{ background: "linear-gradient(150deg,#f7e8e3 0%,#efcdc6 55%,#e9e2f4 100%)" }}
          >
            <BouquetArt
              palette={palettes.peony}
              className="absolute inset-x-0 bottom-6 mx-auto h-[88%]"
            />

            {/* floating proof cards */}
            <div className="absolute -left-6 top-10 hidden sm:flex items-center gap-2.5 rounded-2xl bg-ivory/95 px-4 py-3 shadow-card backdrop-blur animate-float-slow">
              <span className="grid size-9 place-items-center rounded-full bg-blush text-base">📷</span>
              <div className="text-xs">
                <p className="font-semibold text-pine">Photo before delivery</p>
                <p className="text-fawn">approve or adjust</p>
              </div>
            </div>
            <div className="absolute -right-4 bottom-16 hidden sm:flex items-center gap-2.5 rounded-2xl bg-ivory/95 px-4 py-3 shadow-card backdrop-blur animate-float">
              <span className="grid size-9 place-items-center rounded-full bg-lilac text-base">🚚</span>
              <div className="text-xs">
                <p className="font-semibold text-pine">Delivered in 28 min</p>
                <p className="text-fawn">Yunusabad → Chilanzar</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
