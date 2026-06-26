import { describe, expect, it } from "vitest";
import {
  apiCategoryToCategory,
  apiProductToProduct,
} from "./catalog";
import type { ApiCategory, ApiProductListItem } from "./api";

const roses: ApiCategory = {
  id: 1,
  name: "Roses",
  slug: "roses",
  description: "Classic roses",
  image: null,
  product_count: 3,
};

function apiProduct(overrides: Partial<ApiProductListItem> = {}): ApiProductListItem {
  return {
    id: 42,
    name: "Crimson Velvet Rose",
    slug: "crimson-velvet-rose",
    price: "24.99",
    image: "http://localhost:8000/media/products/rose.jpg",
    category: roses.id,
    category_name: roses.name,
    is_available: true,
    is_in_stock: true,
    ...overrides,
  };
}

describe("catalog API adapter", () => {
  it("maps backend categories to storefront category chips", () => {
    expect(apiCategoryToCategory(roses)).toMatchObject({
      id: "roses",
      name: "Roses",
    });
  });

  it("normalizes backend products into card-ready products", () => {
    const product = apiProductToProduct(
      apiProduct(),
      new Map([[roses.id, roses]]),
    );

    expect(product).toMatchObject({
      id: "crimson-velvet-rose",
      backendId: 42,
      category: "roses",
      image: "http://localhost:8000/media/products/rose.jpg",
      isAvailable: true,
      isInStock: true,
      source: "api",
    });
    expect(product.price).toBe(24.99);
    expect(product.palette.petals.length).toBeGreaterThan(0);
  });

  it("derives a category slug when only the category name is present", () => {
    const product = apiProductToProduct(
      apiProduct({
        category: null,
        category_name: "Exotic & Tropical",
      }),
    );

    expect(product.category).toBe("exotic-and-tropical");
  });
});
