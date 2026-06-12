const columns = [
  {
    title: "Flowers",
    links: ["Roses", "Peonies", "Tulips", "Orchids", "Mono bouquets", "Flowers in a box", "Indoor plants"],
  },
  {
    title: "Occasions",
    links: ["Birthday", "Anniversary", "Romantic date", "Wedding", "New baby", "Apology", "Just because"],
  },
  {
    title: "Support",
    links: ["Delivery & payment", "Track my order", "Freshness guarantee", "Refunds", "FAQ", "Contact us"],
  },
];

const socials = [
  {
    name: "Instagram",
    icon: (
      <svg viewBox="0 0 24 24" className="size-4.5" fill="none" stroke="currentColor" strokeWidth="1.7">
        <rect x="3" y="3" width="18" height="18" rx="5" />
        <circle cx="12" cy="12" r="4" />
        <circle cx="17.2" cy="6.8" r="1.1" fill="currentColor" stroke="none" />
      </svg>
    ),
  },
  {
    name: "Telegram",
    icon: (
      <svg viewBox="0 0 24 24" className="size-4.5" fill="currentColor">
        <path d="M21.5 3.6 2.9 10.8c-1 .4-1 1.5 0 1.8l4.6 1.5 1.8 5.6c.3.9 1.4 1 1.9.3l2.6-3.2 4.8 3.5c.8.6 1.9.2 2.1-.8l2.6-14.3c.2-1.1-.8-2-1.8-1.6ZM9.4 13.7l8.6-6.5c.4-.3.8.2.5.5l-7 6.9-.3 3-1.8-3.9Z" />
      </svg>
    ),
  },
  {
    name: "YouTube",
    icon: (
      <svg viewBox="0 0 24 24" className="size-4.5" fill="none" stroke="currentColor" strokeWidth="1.7">
        <rect x="2.5" y="6" width="19" height="12.5" rx="4" />
        <path d="M10.5 9.5v5.5l5-2.75z" fill="currentColor" stroke="none" />
      </svg>
    ),
  },
];

export default function Footer() {
  return (
    <footer className="mt-auto bg-pine text-cream/85">
      <div className="mx-auto max-w-7xl px-4 py-14 grid gap-10 lg:grid-cols-[1.3fr_repeat(3,1fr)_1.2fr]">
        {/* brand */}
        <div>
          <p className="font-display text-3xl font-semibold text-cream">Gulora</p>
          <p className="mt-3 max-w-xs text-sm leading-relaxed text-cream/65">
            A marketplace of independent Tashkent florists. Fresh bouquets,
            gift boxes and plants — same-day, with a photo before delivery.
          </p>
          <div className="mt-5 flex gap-2.5">
            {socials.map((social) => (
              <a
                key={social.name}
                href="#"
                aria-label={social.name}
                className="grid size-10 place-items-center rounded-full border border-cream/20 transition hover:border-cream hover:bg-cream hover:text-pine"
              >
                {social.icon}
              </a>
            ))}
          </div>
        </div>

        {/* link columns */}
        {columns.map((column) => (
          <nav key={column.title} aria-label={column.title}>
            <p className="font-semibold text-cream">{column.title}</p>
            <ul className="mt-4 space-y-2.5 text-sm">
              {column.links.map((link) => (
                <li key={link}>
                  <a href="#" className="text-cream/65 transition hover:text-cream">
                    {link}
                  </a>
                </li>
              ))}
            </ul>
          </nav>
        ))}

        {/* partner CTA */}
        <div className="rounded-3xl bg-cream/10 p-6 self-start">
          <p className="font-display text-lg font-semibold text-cream">
            Become a florist partner
          </p>
          <p className="mt-2 text-sm text-cream/65">
            Own a flower studio in Tashkent? Reach thousands of new customers.
          </p>
          <a
            href="#"
            className="mt-4 inline-block rounded-full bg-coral px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-coraldeep"
          >
            Apply now
          </a>
        </div>
      </div>

      <div className="border-t border-cream/15">
        <div className="mx-auto max-w-7xl px-4 py-5 flex flex-wrap items-center justify-between gap-4 text-xs text-cream/55">
          <p>© {new Date().getFullYear()} Gulora Marketplace. Made with care in Tashkent.</p>
          <div className="flex gap-2">
            {["EN", "RU", "UZ"].map((lang, i) => (
              <button
                key={lang}
                type="button"
                className={`rounded-full px-3 py-1.5 font-semibold transition ${
                  i === 0 ? "bg-cream/15 text-cream" : "hover:text-cream"
                }`}
              >
                {lang}
              </button>
            ))}
            <span className="mx-1 self-center text-cream/25">|</span>
            <button type="button" className="rounded-full bg-cream/15 px-3 py-1.5 font-semibold text-cream">
              $ USD
            </button>
          </div>
        </div>
      </div>
    </footer>
  );
}
