import { occasions } from "@/lib/data";

function MiniFlower({ color, className }: { color: string; className?: string }) {
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true">
      {[0, 72, 144, 216, 288].map((angle) => (
        <ellipse
          key={angle}
          cx="20"
          cy="13"
          rx="6.5"
          ry="4.2"
          fill={color}
          transform={`rotate(${angle} 20 20)`}
        />
      ))}
      <circle cx="20" cy="20" r="4" fill="#fffdf9" opacity="0.85" />
    </svg>
  );
}

export default function GiftFinder() {
  return (
    <section className="mx-auto max-w-7xl px-4 py-16">
      <h2 className="font-display text-3xl sm:text-4xl font-semibold text-pine text-center">
        Find the perfect gift
      </h2>
      <p className="mt-2 text-center text-fawn">
        Tell us the occasion — we&apos;ll suggest the bouquet
      </p>

      <div className="mt-10 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        {occasions.map((occ) => (
          <a
            key={occ.id}
            href="#catalog"
            className={`group relative overflow-hidden rounded-3xl bg-gradient-to-br ${occ.tint} p-5 pt-6 shadow-card transition duration-300 hover:-translate-y-1.5 hover:shadow-petal`}
          >
            <MiniFlower
              color={occ.petalColor}
              className="absolute -right-3 -top-3 size-16 opacity-70 transition duration-500 group-hover:rotate-45 group-hover:scale-125"
            />
            <MiniFlower
              color={occ.petalColor}
              className="absolute -bottom-4 -left-4 size-12 opacity-30"
            />
            <p className="relative font-display text-lg font-semibold leading-tight text-pine">
              {occ.title}
            </p>
            <p className="relative mt-1 text-xs text-ink/60">{occ.subtitle}</p>
            <span className="relative mt-5 inline-flex items-center gap-1 text-xs font-semibold text-pine/80 group-hover:gap-2 transition-all">
              Browse <span aria-hidden="true">→</span>
            </span>
          </a>
        ))}
      </div>
    </section>
  );
}
