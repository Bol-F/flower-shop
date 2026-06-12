import type { CategoryId } from "@/lib/types";

/**
 * Hand-drawn icon set so the marketplace doesn't depend on an icon
 * library. UI icons are single-color strokes; category icons are tiny
 * multi-color illustrations in the blossom palette.
 */

interface IconProps {
  className?: string;
}

/* ── UI icons (stroke, currentColor) ──────────────────────────── */

const stroke = {
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.8,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
};

export function SearchIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 20 20" className={className} {...stroke} aria-hidden="true">
      <circle cx="9" cy="9" r="5.5" />
      <path d="M13.2 13.2 L17 17" />
    </svg>
  );
}

export function HeartIcon({ className, filled = false }: IconProps & { filled?: boolean }) {
  return (
    <svg
      viewBox="0 0 20 20"
      className={className}
      fill={filled ? "currentColor" : "none"}
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M10 17 C4 12.5 2 9.5 2 6.8 C2 4.6 3.7 3 5.8 3 C7.3 3 8.9 3.8 10 5.6 C11.1 3.8 12.7 3 14.2 3 C16.3 3 18 4.6 18 6.8 C18 9.5 16 12.5 10 17 Z" />
    </svg>
  );
}

export function CartIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 20 20" className={className} {...stroke} aria-hidden="true">
      <path d="M6.5 7 V5.5 a3.5 3.5 0 0 1 7 0 V7" />
      <path d="M4 7 h12 l-0.9 9 a2 2 0 0 1 -2 1.8 H6.9 a2 2 0 0 1 -2 -1.8 Z" />
    </svg>
  );
}

export function UserIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 20 20" className={className} {...stroke} aria-hidden="true">
      <circle cx="10" cy="6.5" r="3.2" />
      <path d="M3.8 17 c0.8 -3.4 3.3 -4.8 6.2 -4.8 s5.4 1.4 6.2 4.8" />
    </svg>
  );
}

export function MenuIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 20 20" className={className} {...stroke} aria-hidden="true">
      <path d="M3.5 5.5 H16.5 M3.5 10 H16.5 M3.5 14.5 H16.5" />
    </svg>
  );
}

export function PinIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 20 20" className={className} {...stroke} aria-hidden="true">
      <path d="M10 17.5 C6 13.5 4.5 10.8 4.5 8.4 a5.5 5.5 0 0 1 11 0 C15.5 10.8 14 13.5 10 17.5 Z" />
      <circle cx="10" cy="8.4" r="1.9" />
    </svg>
  );
}

export function StarIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 20 20" className={className} fill="currentColor" aria-hidden="true">
      <path d="M10 1.8 l2.4 5 5.4 0.7 -4 3.8 1 5.4 -4.8 -2.6 -4.8 2.6 1 -5.4 -4 -3.8 5.4 -0.7 Z" />
    </svg>
  );
}

export function BoltIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 20 20" className={className} fill="currentColor" aria-hidden="true">
      <path d="M11.5 1.5 L4 11.5 h4.5 L8 18.5 L16 8.5 h-4.5 Z" />
    </svg>
  );
}

export function CameraIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 20 20" className={className} {...stroke} aria-hidden="true">
      <path d="M3 6.5 h3 l1.3 -2 h5.4 l1.3 2 h3 v9.5 h-14 Z" />
      <circle cx="10" cy="11" r="3" />
    </svg>
  );
}

export function LeafIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 20 20" className={className} {...stroke} aria-hidden="true">
      <path d="M16.5 3.5 C9 4 4.5 8 4.2 16 C12 16.5 16.5 11.5 16.5 3.5 Z" />
      <path d="M4.5 15.5 C8 11.5 11 9 14.5 5.5" />
    </svg>
  );
}

export function TruckIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 20" className={className} {...stroke} aria-hidden="true">
      <path d="M2 4.5 h11.5 v9 H2 Z" />
      <path d="M13.5 7.5 h4.2 L21 11 v2.5 h-7.5" />
      <circle cx="6.2" cy="15.4" r="1.9" />
      <circle cx="17" cy="15.4" r="1.9" />
    </svg>
  );
}

export function PlusIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 20 20" className={className} {...stroke} strokeWidth={2.2} aria-hidden="true">
      <path d="M10 4.5 V15.5 M4.5 10 H15.5" />
    </svg>
  );
}

export function MinusIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 20 20" className={className} {...stroke} strokeWidth={2.2} aria-hidden="true">
      <path d="M4.5 10 H15.5" />
    </svg>
  );
}

export function ChevronIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 20 20" className={className} {...stroke} aria-hidden="true">
      <path d="M6 8 l4 4 4 -4" />
    </svg>
  );
}

export function ArrowRightIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 20 20" className={className} {...stroke} aria-hidden="true">
      <path d="M3.5 10 H16 M11.5 5 L16.5 10 L11.5 15" />
    </svg>
  );
}

export function CloseIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 20 20" className={className} {...stroke} aria-hidden="true">
      <path d="M5 5 L15 15 M15 5 L5 15" />
    </svg>
  );
}

export function TrashIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 20 20" className={className} {...stroke} aria-hidden="true">
      <path d="M4 5.5 h12 M8 5.5 V4 h4 v1.5 M6 5.5 l0.8 11 h6.4 l0.8 -11" />
    </svg>
  );
}

/* ── logo mark ────────────────────────────────────────────────── */

export function LogoMark({ className }: IconProps) {
  return (
    <svg viewBox="0 0 32 32" className={className} aria-hidden="true">
      <circle cx="16" cy="16" r="16" fill="#ff9d68" />
      {[0, 60, 120, 180, 240, 300].map((a) => (
        <ellipse
          key={a}
          cx="16"
          cy="10.5"
          rx="3.4"
          ry="5"
          fill="#fff4ea"
          transform={`rotate(${a} 16 16)`}
        />
      ))}
      <circle cx="16" cy="16" r="3.4" fill="#df622a" />
    </svg>
  );
}

/* ── category illustrations ───────────────────────────────────── */

function RoseIcon() {
  return (
    <svg viewBox="0 0 32 32" className="size-8" aria-hidden="true">
      <path d="M16 18 V28" stroke="#4e8a63" strokeWidth="2" strokeLinecap="round" />
      <path d="M16 24 C13 23 11.5 21.5 11 19" stroke="#4e8a63" strokeWidth="1.8" strokeLinecap="round" fill="none" />
      <circle cx="16" cy="10" r="7" fill="#e0566e" />
      <path d="M16 5.5 a4.5 4.5 0 0 1 0 9 a3 3 0 0 1 0 -6 a1.6 1.6 0 0 1 0 3.2" stroke="#f8c0cb" strokeWidth="1.6" fill="none" strokeLinecap="round" />
    </svg>
  );
}

function TulipIcon() {
  return (
    <svg viewBox="0 0 32 32" className="size-8" aria-hidden="true">
      <path d="M16 16 V28" stroke="#4e8a63" strokeWidth="2" strokeLinecap="round" />
      <path d="M16 23 C12.5 22.5 10.8 20.7 10.5 17.8" stroke="#4e8a63" strokeWidth="1.8" strokeLinecap="round" fill="none" />
      <path d="M9.5 6 C9.5 12 11.5 16 16 16 C20.5 16 22.5 12 22.5 6 C20 8 18.5 8 16 6 C13.5 8 12 8 9.5 6 Z" fill="#ff9d68" />
      <path d="M16 6 V14" stroke="#df622a" strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  );
}

function HatboxIcon() {
  return (
    <svg viewBox="0 0 32 32" className="size-8" aria-hidden="true">
      <circle cx="12" cy="9" r="3.4" fill="#e0566e" />
      <circle cx="19" cy="7.5" r="2.9" fill="#ff9d68" />
      <circle cx="24" cy="10.5" r="2.4" fill="#f2b748" />
      <path d="M7 13 h18 l-1.5 13 a2 2 0 0 1 -2 1.8 h-11 a2 2 0 0 1 -2 -1.8 Z" fill="#b97fc9" />
      <rect x="7" y="13" width="18" height="3.6" rx="1.4" fill="#9d5fb0" />
    </svg>
  );
}

function BasketIcon() {
  return (
    <svg viewBox="0 0 32 32" className="size-8" aria-hidden="true">
      <path d="M9 14 C9 7 23 7 23 14" stroke="#b98a4e" strokeWidth="2" fill="none" strokeLinecap="round" />
      <circle cx="12" cy="11.5" r="2.6" fill="#e0566e" />
      <circle cx="17.5" cy="10" r="2.3" fill="#f2b748" />
      <circle cx="21.5" cy="12" r="2" fill="#ff9d68" />
      <path d="M6.5 14 h19 l-2 11 a2 2 0 0 1 -2 1.6 H10.5 a2 2 0 0 1 -2 -1.6 Z" fill="#d9a866" />
      <path d="M9.5 17.5 h13 M10.2 21.5 h11.6" stroke="#b98a4e" strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  );
}

function CakeIcon() {
  return (
    <svg viewBox="0 0 32 32" className="size-8" aria-hidden="true">
      <rect x="14.8" y="4" width="2.4" height="5" rx="1.2" fill="#f2b748" />
      <circle cx="16" cy="3.6" r="1.6" fill="#ff9d68" />
      <path d="M7 14 h18 v6 a3 3 0 0 1 -3 3 H10 a3 3 0 0 1 -3 -3 Z" fill="#f6a9b8" />
      <path d="M7 14 c2 2.4 4 2.4 6 0 c2 2.4 4 2.4 6 0 c2 2.4 4 2.4 6 0 v3 H7 Z" fill="#fde7ec" />
      <rect x="5.5" y="23" width="21" height="3" rx="1.5" fill="#e0566e" />
    </svg>
  );
}

function HeartsIcon() {
  return (
    <svg viewBox="0 0 32 32" className="size-8" aria-hidden="true">
      <path d="M12 22 C7 18.4 5.5 16 5.5 13.7 C5.5 11.9 6.9 10.5 8.6 10.5 C9.8 10.5 11.1 11.2 12 12.6 C12.9 11.2 14.2 10.5 15.4 10.5 C17.1 10.5 18.5 11.9 18.5 13.7 C18.5 16 17 18.4 12 22 Z" fill="#e0566e" />
      <path d="M21 17.5 C17.6 15 16.5 13.3 16.5 11.7 C16.5 10.4 17.5 9.5 18.7 9.5 C19.5 9.5 20.4 10 21 11 C21.6 10 22.5 9.5 23.3 9.5 C24.5 9.5 25.5 10.4 25.5 11.7 C25.5 13.3 24.4 15 21 17.5 Z" fill="#ff9d68" />
    </svg>
  );
}

function RingIcon() {
  return (
    <svg viewBox="0 0 32 32" className="size-8" aria-hidden="true">
      <circle cx="16" cy="19" r="7" stroke="#e3b04b" strokeWidth="2.6" fill="none" />
      <path d="M13 8.5 L16 5 L19 8.5 L16 12 Z" fill="#a9c8e8" stroke="#86aedd" strokeWidth="1" strokeLinejoin="round" />
      <circle cx="11" cy="13.5" r="1.6" fill="#f6a9b8" />
      <circle cx="21" cy="13.5" r="1.6" fill="#f6a9b8" />
    </svg>
  );
}

function PlantIcon() {
  return (
    <svg viewBox="0 0 32 32" className="size-8" aria-hidden="true">
      <path d="M16 18 C16 11 13 8 8 7 C8 13 10.5 16.5 16 18 Z" fill="#4e8a63" />
      <path d="M16 18 C16 12.5 18.5 9.5 24 8.5 C23.8 14 21 17 16 18 Z" fill="#7fb88f" />
      <path d="M16 12 V20" stroke="#3f7351" strokeWidth="1.6" strokeLinecap="round" />
      <path d="M10 20 h12 l-1.4 7.2 a1.8 1.8 0 0 1 -1.8 1.4 h-5.6 a1.8 1.8 0 0 1 -1.8 -1.4 Z" fill="#d9794e" />
      <rect x="9.4" y="20" width="13.2" height="2.6" rx="1.3" fill="#c4623a" />
    </svg>
  );
}

function GiftIcon() {
  return (
    <svg viewBox="0 0 32 32" className="size-8" aria-hidden="true">
      <rect x="6.5" y="13" width="19" height="13" rx="2" fill="#8d77c9" />
      <rect x="6" y="9.5" width="20" height="5" rx="1.8" fill="#a995dd" />
      <rect x="14.4" y="9.5" width="3.2" height="16.5" fill="#ffd9bf" />
      <path d="M16 9.5 C12 9.5 10.5 7.5 11.5 5.5 C12.5 3.8 15.2 4.6 16 7.8 C16.8 4.6 19.5 3.8 20.5 5.5 C21.5 7.5 20 9.5 16 9.5 Z" fill="#ff9d68" />
    </svg>
  );
}

function BalloonsIcon() {
  return (
    <svg viewBox="0 0 32 32" className="size-8" aria-hidden="true">
      <ellipse cx="10.5" cy="10" rx="4.4" ry="5.4" fill="#ff9d68" />
      <ellipse cx="21" cy="8.5" rx="4" ry="5" fill="#86aedd" />
      <ellipse cx="16" cy="14.5" rx="3.6" ry="4.4" fill="#f6a9b8" />
      <path d="M10.5 15.5 C11.5 20 13 23 15 27 M21 13.5 C20 19 18.5 22.5 16.5 27 M16 19 L15.8 27" stroke="#968d80" strokeWidth="1.2" fill="none" strokeLinecap="round" />
      <ellipse cx="9" cy="8" rx="1.2" ry="2" fill="#ffd9bf" transform="rotate(-20 9 8)" />
    </svg>
  );
}

export const CATEGORY_ICONS: Record<CategoryId, () => React.ReactElement> = {
  roses: RoseIcon,
  mono: TulipIcon,
  box: HatboxIcon,
  baskets: BasketIcon,
  birthday: CakeIcon,
  romantic: HeartsIcon,
  wedding: RingIcon,
  plants: PlantIcon,
  gifts: GiftIcon,
  balloons: BalloonsIcon,
};
