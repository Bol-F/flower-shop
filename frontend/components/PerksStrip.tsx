import { BoltIcon, CameraIcon, LeafIcon, TruckIcon } from "./icons";

const perks = [
  {
    icon: BoltIcon,
    title: "Fast delivery",
    text: "Same-day courier windows across Tashkent demo zones",
    tint: "bg-blush text-raspberry",
  },
  {
    icon: CameraIcon,
    title: "Ready for photos",
    text: "Product pages, checkout, and staff screens are screenshot-ready",
    tint: "bg-berrysoft text-berry",
  },
  {
    icon: LeafIcon,
    title: "Stock-aware",
    text: "Low-stock and out-of-stock products are visible to staff",
    tint: "bg-mint text-leaf",
  },
  {
    icon: TruckIcon,
    title: "Complete workflow",
    text: "Orders, payments, support, and notifications stay connected",
    tint: "bg-lilac text-iris",
  },
];

export default function PerksStrip() {
  return (
    <section aria-label="Why Bloom and Petal" className="mx-auto max-w-7xl px-4 py-10">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {perks.map(({ icon: Icon, title, text, tint }) => (
          <div
            key={title}
            className="group flex items-center gap-4 rounded-3xl bg-card p-5 shadow-soft transition duration-300 hover:-translate-y-1"
          >
            <span
              className={`grid size-12 shrink-0 place-items-center rounded-2xl transition duration-300 group-hover:scale-110 group-hover:-rotate-6 ${tint}`}
            >
              <Icon className="size-5.5" />
            </span>
            <div>
              <p className="text-sm font-bold">{title}</p>
              <p className="mt-0.5 text-xs leading-snug text-stone">{text}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
