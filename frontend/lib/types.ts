export interface BouquetPalette {
  /** petal colors, cycled across blooms */
  petals: string[];
  /** flower center color */
  center: string;
  /** card image-area background (CSS gradient) */
  backdrop: string;
}

export interface Product {
  id: string;
  name: string;
  shop: string;
  price: number;
  oldPrice?: number;
  rating: number;
  reviews: number;
  badges: ProductBadge[];
  deliveryToday: boolean;
  isNew: boolean;
  popularity: number;
  palette: BouquetPalette;
}

export type ProductBadge =
  | { kind: "discount"; label: string }
  | { kind: "today"; label: string }
  | { kind: "lastone"; label: string };

export interface Category {
  id: string;
  name: string;
  emoji: string;
  tint: string;
}

export interface Review {
  id: string;
  name: string;
  date: string;
  rating: number;
  text: string;
  shop: string;
  palette: BouquetPalette;
}

export interface Occasion {
  id: string;
  title: string;
  subtitle: string;
  tint: string;
  petalColor: string;
}
