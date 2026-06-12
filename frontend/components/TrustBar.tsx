import { trustPoints } from "@/lib/data";

export default function TrustBar() {
  return (
    <div className="bg-pine text-cream/90 text-xs sm:text-sm">
      <div className="mx-auto max-w-7xl px-4 py-2 flex items-center justify-between gap-6 overflow-x-auto no-scrollbar">
        {trustPoints.map((point) => (
          <span
            key={point.text}
            className="flex items-center gap-1.5 whitespace-nowrap"
          >
            <span aria-hidden="true">{point.icon}</span>
            {point.text}
          </span>
        ))}
      </div>
    </div>
  );
}
