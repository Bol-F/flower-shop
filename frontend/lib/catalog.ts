import {
  API_BASE,
  fetchCategories,
  fetchProduct,
  fetchProducts,
  type ApiCategory,
  type ApiProductBase,
  type ApiProductDetail,
  type ApiProductListItem,
} from "./api";
import { categories as fallbackCategories, palettes, products as fallbackProducts } from "./data";
import type { BouquetPalette, Category, Product } from "./types";

const categoryTints = [
  "#fde7ec",
  "#fff0db",
  "#ffeadb",
  "#f1ecdf",
  "#fde9e0",
  "#fbe3e7",
  "#f5efe6",
  "#e6f3ea",
  "#f0ebfa",
  "#e9f2fb",
];

function labelToSlug(value: string | null | undefined): string {
  return (value || "flowers")
    .toLowerCase()
    .trim()
    .replace(/&/g, "and")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function numberFromPrice(value: string | number): number {
  const parsed = typeof value === "number" ? value : Number.parseFloat(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

export function resolveApiMediaUrl(value: string | null): string | null {
  if (!value) return null;
  try {
    return new URL(value, `${API_BASE}/`).toString();
  } catch {
    return null;
  }
}

function paletteFor(product: ApiProductBase): BouquetPalette {
  const text = `${product.name} ${product.slug} ${product.category_name ?? ""}`.toLowerCase();
  if (text.includes("red") || text.includes("crimson")) return palettes.red;
  if (text.includes("white") || text.includes("champagne")) return palettes.white;
  if (text.includes("pink") || text.includes("peony")) return palettes.peony;
  if (text.includes("sunflower") || text.includes("yellow")) return palettes.sunflower;
  if (text.includes("tulip") || text.includes("orange")) return palettes.tulip;
  if (text.includes("orchid") || text.includes("purple")) return palettes.orchid;
  if (text.includes("wild") || text.includes("meadow")) return palettes.meadow;
  if (text.includes("lavender") || text.includes("blue")) return palettes.lavender;

  const keys = Object.keys(palettes) as Array<keyof typeof palettes>;
  return palettes[keys[product.id % keys.length]];
}

function compositionFor(product: ApiProductBase, detail?: ApiProductDetail): string[] {
  const category = detail?.category?.name ?? product.category_name ?? "Fresh flowers";
  const firstSentence = detail?.description?.split(/[.!?]/).find(Boolean)?.trim();
  return [category, firstSentence && firstSentence.length < 60 ? firstSentence : null].filter(
    (item): item is string => Boolean(item),
  );
}

export function apiCategoryToCategory(category: ApiCategory, index = 0): Category {
  const fallback = fallbackCategories.find((item) => item.id === category.slug);
  return {
    id: category.slug,
    name: category.name,
    tint: fallback?.tint ?? categoryTints[index % categoryTints.length],
  };
}

export function apiProductToProduct(
  product: ApiProductListItem | ApiProductDetail,
  categoryById: Map<number, ApiCategory> = new Map(),
  detail?: ApiProductDetail,
): Product {
  const category =
    detail?.category ??
    (typeof product.category === "number" ? categoryById.get(product.category) : product.category);
  const categorySlug = category?.slug ?? labelToSlug(product.category_name);
  const mock = fallbackProducts.find((item) => item.id === product.slug);
  const price = numberFromPrice(product.price);
  const stock = detail?.stock ?? product.stock_quantity;
  // The API has one price and stock count per product, not purchasable size variants.
  const hasSizes = false;
  const createdAt = Date.parse(product.created_at);
  const isNew = Number.isFinite(createdAt) && Date.now() - createdAt < 30 * 24 * 60 * 60 * 1000;

  return {
    id: product.slug,
    backendId: product.id,
    slug: product.slug,
    name: product.name,
    shop: product.vendor_name || "Bloom & Petal",
    price,
    oldPrice: undefined,
    rating: product.rating_average,
    reviews: product.rating_count,
    category: categorySlug,
    city: product.city_slug,
    vendor: product.vendor_slug,
    deliveryMins: null,
    deliveryToday: null,
    isNew,
    popularity: product.rating_count,
    description:
      detail?.description || `${product.name} from ${product.vendor_name || "Bloom & Petal"}.`,
    composition: compositionFor(product, detail),
    hasSizes,
    palette: mock?.palette ?? paletteFor(product),
    image: resolveApiMediaUrl(product.image),
    stock,
    isAvailable: product.is_available,
    isInStock: product.is_in_stock,
    source: "api",
  };
}

export async function loadCatalogCategories(): Promise<Category[]> {
  const categories = await fetchCategories();
  return categories.map(apiCategoryToCategory);
}

export async function loadCatalogProducts(city?: string | null): Promise<Product[]> {
  const [categories, products] = await Promise.all([
    fetchCategories(),
    fetchProducts({ page_size: 100, city }),
  ]);
  const categoryById = new Map(categories.map((category) => [category.id, category]));
  return products.map((product) => apiProductToProduct(product, categoryById));
}

export async function loadCatalogProduct(slug: string): Promise<Product> {
  const product = await fetchProduct(slug);
  const categoryById = new Map<number, ApiCategory>();
  if (product.category) categoryById.set(product.category.id, product.category);
  return apiProductToProduct(product, categoryById, product);
}

export function fallbackProduct(id: string): Product | undefined {
  const product = fallbackProducts.find((item) => item.id === id);
  return product ? { ...product, slug: product.id, source: "mock" } : undefined;
}

export const fallbackCatalogProducts: Product[] = fallbackProducts.map((product) => ({
  ...product,
  slug: product.id,
  source: "mock",
}));

export const fallbackCatalogCategories: Category[] = fallbackCategories;
