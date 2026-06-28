import {
  fetchCategories,
  fetchProduct,
  fetchProducts,
  type ApiCategory,
  type ApiProductBase,
  type ApiProductDetail,
  type ApiProductListItem,
} from "./api";
import {
  categories as fallbackCategories,
  palettes,
  products as fallbackProducts,
} from "./data";
import type { BouquetPalette, Category, Product } from "./types";

const shops = ["Atelier Bloom", "Bahor Flowers", "Chinor Garden", "Lola Market"];

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
  return [
    category,
    "Fresh stems",
    firstSentence && firstSentence.length < 36 ? firstSentence : "Gift wrap",
    "Care instructions",
  ].filter(Boolean);
}

export function apiCategoryToCategory(
  category: ApiCategory,
  index = 0,
): Category {
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
    (typeof product.category === "number"
      ? categoryById.get(product.category)
      : product.category);
  const categorySlug = category?.slug ?? labelToSlug(product.category_name);
  const mock = fallbackProducts.find((item) => item.id === product.slug);
  const price = numberFromPrice(product.price);
  const stock = detail?.stock ?? product.stock_quantity;

  if (mock) {
    return {
      ...mock,
      backendId: product.id,
      id: product.slug,
      slug: product.slug,
      description: detail?.description || mock.description,
      price,
    category: categorySlug,
    city: product.city_slug,
    vendor: product.vendor_slug,
    image: product.image,
      stock,
      isAvailable: product.is_available,
      isInStock: product.is_in_stock,
      source: "api",
    };
  }

  const hasSizes = !/(plant|pot|potted|dome|preserved|orchid)/i.test(product.name);

  return {
    id: product.slug,
    backendId: product.id,
    slug: product.slug,
    name: product.name,
    shop: shops[product.id % shops.length],
    price,
    oldPrice: product.id % 4 === 0 ? Math.round(price * 1.15) : undefined,
    rating: Math.min(5, 4.5 + (product.id % 6) / 10),
    reviews: 24 + ((product.id * 17) % 220),
    category: categorySlug,
    city: product.city_slug,
    vendor: product.vendor_slug,
    deliveryMins: 60 + (product.id % 5) * 15,
    deliveryToday: product.is_in_stock && product.id % 3 !== 0,
    isNew: product.id % 4 === 0,
    popularity: 60 + ((product.id * 11) % 40),
    description:
      detail?.description ||
      `${product.name} is prepared by a local Bloom & Petal florist and delivered fresh in Tashkent.`,
    composition: compositionFor(product, detail),
    hasSizes,
    palette: paletteFor(product),
    image: product.image,
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
