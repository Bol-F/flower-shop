export interface BouquetPalette {
  /** petal colors, cycled across blooms */
  petals: string[];
  /** flower center color */
  center: string;
  /** card image-area background (CSS gradient) */
  backdrop: string;
}

export type CategoryId = string;

export interface Product {
  id: string;
  /** Numeric database id when the product comes from the Django API. */
  backendId?: number;
  slug?: string;
  name: string;
  shop: string;
  /** base price in USD — converted to UZS client-side */
  price: number;
  oldPrice?: number;
  rating: number;
  reviews: number;
  category: CategoryId;
  /** courier estimate when ordering now */
  deliveryMins: number;
  deliveryToday: boolean;
  isNew: boolean;
  popularity: number;
  description: string;
  composition: string[];
  /** bouquets come in S/M/L; plants & gifts are one size */
  hasSizes: boolean;
  palette: BouquetPalette;
  image?: string | null;
  stock?: number;
  isAvailable?: boolean;
  isInStock?: boolean;
  source?: "api" | "mock";
}

export interface Category {
  id: CategoryId;
  name: string;
  /** soft circle background behind the icon */
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

export type Currency = "USD" | "UZS";

export type Language = "EN" | "RU" | "UZ";

export interface BouquetSize {
  id: "S" | "M" | "L";
  label: string;
  multiplier: number;
}
