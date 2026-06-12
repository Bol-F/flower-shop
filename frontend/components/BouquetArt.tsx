import type { BouquetPalette } from "@/lib/types";

/**
 * Original illustrated bouquet, drawn in SVG and recolored per product.
 * Keeps the whole catalog self-contained — no external image assets.
 */

interface BloomProps {
  cx: number;
  cy: number;
  r: number;
  petal: string;
  center: string;
}

function Bloom({ cx, cy, r, petal, center }: BloomProps) {
  const petalRx = r * 0.62;
  const petalRy = r * 0.4;
  return (
    <g>
      {[0, 60, 120, 180, 240, 300].map((angle) => (
        <ellipse
          key={angle}
          cx={cx}
          cy={cy - r * 0.55}
          rx={petalRx}
          ry={petalRy}
          fill={petal}
          transform={`rotate(${angle} ${cx} ${cy})`}
        />
      ))}
      <circle cx={cx} cy={cy} r={r * 0.34} fill={center} opacity={0.9} />
      <circle cx={cx - r * 0.1} cy={cy - r * 0.12} r={r * 0.12} fill="#fff" opacity={0.35} />
    </g>
  );
}

const BLOOMS: Array<[number, number, number]> = [
  // [cx, cy, r] — composed once so every bouquet shares one silhouette
  [50, 34, 12.5],
  [30, 44, 11],
  [70, 44, 11],
  [38, 58, 10],
  [62, 58, 10],
  [50, 50, 9],
];

export default function BouquetArt({
  palette,
  className,
}: {
  palette: BouquetPalette;
  className?: string;
}) {
  const { petals, center } = palette;
  return (
    <svg viewBox="0 0 100 126" className={className} aria-hidden="true">
      {/* stems */}
      <g stroke="#57755f" strokeWidth="1.6" strokeLinecap="round" fill="none">
        <path d="M50 44 L50 96" />
        <path d="M31 52 Q40 72 48 96" />
        <path d="M69 52 Q60 72 52 96" />
        <path d="M39 64 Q45 80 50 96" />
        <path d="M61 64 Q55 80 50 96" />
      </g>
      {/* leaves */}
      <g fill="#7e9a78">
        <ellipse cx="27" cy="63" rx="7" ry="3.2" transform="rotate(-38 27 63)" />
        <ellipse cx="73" cy="63" rx="7" ry="3.2" transform="rotate(38 73 63)" />
        <ellipse cx="35" cy="76" rx="6" ry="2.8" transform="rotate(-30 35 76)" />
        <ellipse cx="65" cy="76" rx="6" ry="2.8" transform="rotate(30 65 76)" />
      </g>
      {/* blooms — colors cycle through the product palette */}
      {BLOOMS.map(([cx, cy, r], i) => (
        <Bloom
          key={i}
          cx={cx}
          cy={cy}
          r={r}
          petal={petals[i % petals.length]}
          center={center}
        />
      ))}
      {/* kraft wrap */}
      <path
        d="M30 78 L50 122 L70 78 L62 86 L50 80 L38 86 Z"
        fill="#eadfcb"
        stroke="#d9cbb2"
        strokeWidth="1"
        strokeLinejoin="round"
      />
      <path d="M30 78 L50 122 L42 84 Z" fill="#e0d2b8" opacity={0.8} />
      {/* ribbon */}
      <rect x="42" y="88" width="16" height="4.5" rx="2.2" fill="#c96f7e" />
    </svg>
  );
}
