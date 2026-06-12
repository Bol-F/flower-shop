const features = [
  {
    title: "Fresh from local florists",
    text: "Every bouquet is composed to order by an independent Tashkent studio — never from cold storage.",
    icon: (
      <svg viewBox="0 0 24 24" className="size-6" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 22 V12" />
        <path d="M12 12 C7 12 4 9 4 4 C9 4 12 7 12 12 Z" />
        <path d="M12 12 C17 12 20 9 20 4 C15 4 12 7 12 12 Z" />
      </svg>
    ),
  },
  {
    title: "Photo before delivery",
    text: "See the exact bouquet before the courier leaves. Ask for changes — the florist adjusts on the spot.",
    icon: (
      <svg viewBox="0 0 24 24" className="size-6" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="7" width="18" height="13" rx="3" />
        <path d="M8.5 7 L10 4.5 h4 L15.5 7" />
        <circle cx="12" cy="13.5" r="3.5" />
      </svg>
    ),
  },
  {
    title: "Fast across Tashkent",
    text: "Couriers in every district. Average door-to-door time is 42 minutes; the record is 28.",
    icon: (
      <svg viewBox="0 0 24 24" className="size-6" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
        <path d="M13 3 L4 14 h6 l-1 7 9-11 h-6 Z" />
      </svg>
    ),
  },
  {
    title: "Secure payment & tracking",
    text: "Pay by card or in cash, follow the courier live, and get an instant refund if anything goes wrong.",
    icon: (
      <svg viewBox="0 0 24 24" className="size-6" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 3 L20 6 v5 c0 5 -3.5 8.5 -8 10 -4.5 -1.5 -8 -5 -8 -10 V6 Z" />
        <path d="M9 12 l2 2 4 -4.5" />
      </svg>
    ),
  },
];

export default function WhyChooseUs() {
  return (
    <section className="mx-auto max-w-7xl px-4 py-16">
      <h2 className="font-display text-3xl sm:text-4xl font-semibold text-pine text-center">
        Why people choose Gulora
      </h2>

      <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {features.map((feature) => (
          <div
            key={feature.title}
            className="group rounded-3xl bg-ivory p-7 shadow-card transition duration-300 hover:-translate-y-1.5 hover:shadow-petal"
          >
            <span className="grid size-12 place-items-center rounded-2xl bg-blush text-rosedeep transition group-hover:bg-pine group-hover:text-cream">
              {feature.icon}
            </span>
            <h3 className="mt-5 font-display text-xl font-semibold text-pine">
              {feature.title}
            </h3>
            <p className="mt-2 text-sm leading-relaxed text-fawn">{feature.text}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
