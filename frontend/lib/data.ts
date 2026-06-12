import type { BouquetPalette, Category, Occasion, Product, Review } from "./types";

/* ── shared palettes for the illustrated bouquets ─────────────── */

export const palettes = {
  pinkRose: {
    petals: ["#e8a2ae", "#d97f90", "#f2c4cb"],
    center: "#a84d60",
    backdrop: "linear-gradient(160deg,#fbeff1 0%,#f4d8dc 100%)",
  },
  white: {
    petals: ["#fdfaf4", "#f3ecdf", "#faf4e9"],
    center: "#d9b96a",
    backdrop: "linear-gradient(160deg,#f6f3ec 0%,#e9e2d2 100%)",
  },
  peony: {
    petals: ["#f4b8c4", "#ee9cb0", "#f9d3da"],
    center: "#c75a76",
    backdrop: "linear-gradient(160deg,#fdf1f4 0%,#f6d9e0 100%)",
  },
  red: {
    petals: ["#c9474f", "#a82f3c", "#df6c70"],
    center: "#7c1f2b",
    backdrop: "linear-gradient(160deg,#f9e8e6 0%,#efc9c4 100%)",
  },
  lavender: {
    petals: ["#b9a8d8", "#9d87c7", "#d4c8e8"],
    center: "#6f5a9c",
    backdrop: "linear-gradient(160deg,#f3effa 0%,#ddd3ee 100%)",
  },
  tulip: {
    petals: ["#f2b748", "#e89a3c", "#f8d278"],
    center: "#b56a1e",
    backdrop: "linear-gradient(160deg,#fbf3e2 0%,#f3e0b9 100%)",
  },
  orchid: {
    petals: ["#e6d9f2", "#cdb4e4", "#f4eefa"],
    center: "#8f6bb8",
    backdrop: "linear-gradient(160deg,#f6f2fa 0%,#e5dbf0 100%)",
  },
  mixBox: {
    petals: ["#e8a2ae", "#f2b748", "#b9a8d8"],
    center: "#a84d60",
    backdrop: "linear-gradient(160deg,#fdf4ec 0%,#f5dfd2 100%)",
  },
  garden: {
    petals: ["#ee9cb0", "#f2b748", "#fdfaf4"],
    center: "#c75a76",
    backdrop: "linear-gradient(160deg,#f2f5ec 0%,#dde7d2 100%)",
  },
  wedding: {
    petals: ["#fdfaf4", "#f2dfe4", "#efcdc6"],
    center: "#c0a26a",
    backdrop: "linear-gradient(160deg,#faf7f1 0%,#ece2da 100%)",
  },
} satisfies Record<string, BouquetPalette>;

/* ── catalog products ─────────────────────────────────────────── */

export const products: Product[] = [
  {
    id: "pink-rose-harmony",
    name: "Pink Rose Harmony",
    shop: "Atelier Bloom",
    price: 49,
    oldPrice: 58,
    rating: 4.9,
    reviews: 214,
    badges: [
      { kind: "discount", label: "-15%" },
      { kind: "today", label: "Today delivery" },
    ],
    deliveryToday: true,
    isNew: false,
    popularity: 98,
    palette: palettes.pinkRose,
  },
  {
    id: "white-dream",
    name: "White Dream Bouquet",
    shop: "Gulnora Flowers",
    price: 64,
    rating: 4.8,
    reviews: 167,
    badges: [{ kind: "today", label: "Today delivery" }],
    deliveryToday: true,
    isNew: false,
    popularity: 91,
    palette: palettes.white,
  },
  {
    id: "peony-cloud",
    name: "Peony Cloud",
    shop: "Chinor Garden",
    price: 89,
    oldPrice: 105,
    rating: 5.0,
    reviews: 96,
    badges: [
      { kind: "discount", label: "-15%" },
      { kind: "lastone", label: "Last one" },
    ],
    deliveryToday: false,
    isNew: true,
    popularity: 95,
    palette: palettes.peony,
  },
  {
    id: "romantic-red",
    name: "Romantic Red Roses",
    shop: "Atelier Bloom",
    price: 75,
    rating: 4.9,
    reviews: 322,
    badges: [{ kind: "today", label: "Today delivery" }],
    deliveryToday: true,
    isNew: false,
    popularity: 100,
    palette: palettes.red,
  },
  {
    id: "lavender-basket",
    name: "Lavender Basket",
    shop: "Sayyora Studio",
    price: 54,
    rating: 4.7,
    reviews: 88,
    badges: [],
    deliveryToday: false,
    isNew: true,
    popularity: 74,
    palette: palettes.lavender,
  },
  {
    id: "sunshine-tulips",
    name: "Sunshine Tulips",
    shop: "Lola Market",
    price: 39,
    oldPrice: 46,
    rating: 4.8,
    reviews: 145,
    badges: [
      { kind: "discount", label: "-15%" },
      { kind: "today", label: "Today delivery" },
    ],
    deliveryToday: true,
    isNew: false,
    popularity: 87,
    palette: palettes.tulip,
  },
  {
    id: "orchid-elegance",
    name: "Orchid Elegance",
    shop: "Sayyora Studio",
    price: 96,
    rating: 4.9,
    reviews: 61,
    badges: [{ kind: "lastone", label: "Last one" }],
    deliveryToday: false,
    isNew: true,
    popularity: 79,
    palette: palettes.orchid,
  },
  {
    id: "birthday-box",
    name: "Birthday Flower Box",
    shop: "Lola Market",
    price: 59,
    rating: 4.8,
    reviews: 198,
    badges: [{ kind: "today", label: "Today delivery" }],
    deliveryToday: true,
    isNew: false,
    popularity: 93,
    palette: palettes.mixBox,
  },
  {
    id: "mothers-garden",
    name: "Mother's Day Garden",
    shop: "Chinor Garden",
    price: 69,
    oldPrice: 79,
    rating: 4.9,
    reviews: 124,
    badges: [{ kind: "discount", label: "-12%" }],
    deliveryToday: true,
    isNew: false,
    popularity: 85,
    palette: palettes.garden,
  },
  {
    id: "premium-wedding",
    name: "Premium Wedding Bouquet",
    shop: "Gulnora Flowers",
    price: 149,
    rating: 5.0,
    reviews: 47,
    badges: [],
    deliveryToday: false,
    isNew: true,
    popularity: 82,
    palette: palettes.wedding,
  },
];

/* ── category chips ───────────────────────────────────────────── */

export const categories: Category[] = [
  { id: "roses", name: "Roses", emoji: "🌹", tint: "bg-blush" },
  { id: "mono", name: "Mono Bouquets", emoji: "🌷", tint: "bg-lilac" },
  { id: "box", name: "Flowers in a Box", emoji: "🎁", tint: "bg-beige" },
  { id: "baskets", name: "Flower Baskets", emoji: "🧺", tint: "bg-blush" },
  { id: "birthday", name: "Birthday Flowers", emoji: "🎂", tint: "bg-lilac" },
  { id: "romantic", name: "Romantic Bouquets", emoji: "💕", tint: "bg-blush" },
  { id: "wedding", name: "Wedding Bouquets", emoji: "💍", tint: "bg-beige" },
  { id: "plants", name: "Indoor Plants", emoji: "🪴", tint: "bg-lilac" },
  { id: "gifts", name: "Gift Sets", emoji: "🍫", tint: "bg-beige" },
  { id: "balloons", name: "Balloons", emoji: "🎈", tint: "bg-blush" },
];

/* ── gift finder occasions ────────────────────────────────────── */

export const occasions: Occasion[] = [
  {
    id: "birthday",
    title: "For birthday",
    subtitle: "Bright & joyful",
    tint: "from-[#fbf3e2] to-[#f3e0b9]",
    petalColor: "#f2b748",
  },
  {
    id: "girlfriend",
    title: "For girlfriend",
    subtitle: "Sweet & romantic",
    tint: "from-[#fdf1f4] to-[#f6d9e0]",
    petalColor: "#ee9cb0",
  },
  {
    id: "mother",
    title: "For mother",
    subtitle: "Warm & tender",
    tint: "from-[#f2f5ec] to-[#dde7d2]",
    petalColor: "#a7bca1",
  },
  {
    id: "anniversary",
    title: "For anniversary",
    subtitle: "Deep & elegant",
    tint: "from-[#f9e8e6] to-[#efc9c4]",
    petalColor: "#c9474f",
  },
  {
    id: "apology",
    title: "For apology",
    subtitle: "Gentle & sincere",
    tint: "from-[#f3effa] to-[#ddd3ee]",
    petalColor: "#b9a8d8",
  },
  {
    id: "wedding",
    title: "For wedding",
    subtitle: "Pure & timeless",
    tint: "from-[#faf7f1] to-[#ece2da]",
    petalColor: "#e8d3b4",
  },
];

/* ── reviews ──────────────────────────────────────────────────── */

export const reviews: Review[] = [
  {
    id: "r1",
    name: "Madina K.",
    date: "May 28, 2026",
    rating: 5,
    text: "Ordered at noon, delivered by 2pm with a photo before handover. The peonies were even fresher than the picture — my mom cried happy tears.",
    shop: "Chinor Garden",
    palette: palettes.peony,
  },
  {
    id: "r2",
    name: "Timur A.",
    date: "June 2, 2026",
    rating: 5,
    text: "The photo-before-delivery feature saved me. I asked to swap the ribbon color and the florist did it in minutes. Flawless anniversary.",
    shop: "Atelier Bloom",
    palette: palettes.red,
  },
  {
    id: "r3",
    name: "Nilufar S.",
    date: "June 7, 2026",
    rating: 4,
    text: "Beautiful tulips and very fast courier — 40 minutes across the whole city. Would love more vase options at checkout.",
    shop: "Lola Market",
    palette: palettes.tulip,
  },
  {
    id: "r4",
    name: "Sardor R.",
    date: "June 10, 2026",
    rating: 5,
    text: "Built a custom bouquet for our wedding rehearsal. The builder made it easy to stay on budget and the result looked far more expensive.",
    shop: "Gulnora Flowers",
    palette: palettes.wedding,
  },
];

/* ── header / trust bar copy ──────────────────────────────────── */

export const trustPoints = [
  { icon: "⚡", text: "Delivery from 30 minutes" },
  { icon: "📷", text: "Photo before delivery" },
  { icon: "🌿", text: "Fresh flowers guarantee" },
  { icon: "🚚", text: "Same-day delivery in Tashkent" },
];
