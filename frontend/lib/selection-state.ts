import type { GuestSelectionMergePayload } from "./api";
import type { Product } from "./types";

/** Selection snapshots carry no tokens or personal details. */
export interface SelectionState {
  favorites: string[];
  favoriteProducts: Record<string, Product>;
  cart: Record<string, number>;
  cartProducts: Record<string, Product>;
}

export interface PendingGuestMerge {
  payload: GuestSelectionMergePayload;
  selection: SelectionState;
}

export function emptySelection(): SelectionState {
  return { favorites: [], favoriteProducts: {}, cart: {}, cartProducts: {} };
}

export function stockLimit(product?: Product): number {
  if (product?.isAvailable === false || product?.isInStock === false) return 0;
  return typeof product?.stock === "number" && Number.isFinite(product.stock)
    ? Math.min(999, Math.max(0, Math.floor(product.stock)))
    : 999;
}

export function selectionFrom(value: unknown): SelectionState {
  const result = emptySelection();
  if (!value || typeof value !== "object") return result;
  const source = value as Partial<SelectionState>;
  if (Array.isArray(source.favorites)) {
    result.favorites = [...new Set(source.favorites.filter(validId))].slice(0, 100);
  }
  for (const key of ["cartProducts", "favoriteProducts"] as const) {
    const products = source[key];
    if (!products || typeof products !== "object") continue;
    for (const [id, product] of Object.entries(products)) {
      if (validId(id) && product && product.id === id && typeof product.name === "string") {
        result[key][id] = product;
      }
    }
  }
  if (source.cart && typeof source.cart === "object") {
    for (const [id, qty] of Object.entries(source.cart).slice(0, 100)) {
      if (validId(id) && Number.isSafeInteger(qty) && qty > 0) {
        result.cart[id] = Math.min(qty, 999);
      }
    }
  }
  return result;
}

function validId(value: unknown): value is string {
  return typeof value === "string" && value.length > 0 && value.length <= 200;
}

export function hasSelections(selection: SelectionState): boolean {
  return selection.favorites.length > 0 || Object.keys(selection.cart).length > 0;
}

export function newGuestMerge(selection: SelectionState): PendingGuestMerge | null {
  if (!hasSelections(selection)) return null;
  const snapshot = selectionFrom(selection);
  return {
    payload: {
      merge_id: crypto.randomUUID(),
      items: Object.entries(snapshot.cart).map(([id, quantity]) => ({
        product_slug: snapshot.cartProducts[id]?.slug || id,
        quantity,
      })),
      wishlist: snapshot.favorites.map((id) => snapshot.favoriteProducts[id]?.slug || id),
    },
    selection: snapshot,
  };
}

export function readPendingGuestMerges(raw: string | null): PendingGuestMerge[] {
  if (!raw) return [];
  try {
    const parsed: unknown = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed
      .filter((item): item is PendingGuestMerge => {
        const payload = item?.payload as GuestSelectionMergePayload | undefined;
        return Boolean(
          payload &&
          typeof payload.merge_id === "string" &&
          /^[0-9a-f-]{36}$/i.test(payload.merge_id) &&
          Array.isArray(payload.items) &&
          payload.items.length <= 100 &&
          payload.items.every(
            (entry) =>
              validId(entry.product_slug) &&
              Number.isSafeInteger(entry.quantity) &&
              entry.quantity > 0 &&
              entry.quantity <= 999,
          ) &&
          Array.isArray(payload.wishlist) &&
          payload.wishlist.length <= 100 &&
          payload.wishlist.every(validId),
        );
      })
      .map((item) => ({ payload: item.payload, selection: selectionFrom(item.selection) }));
  } catch {
    return [];
  }
}

export function pendingSelection(pending: PendingGuestMerge[]): SelectionState {
  const result = emptySelection();
  for (const { selection } of pending) {
    Object.assign(result.cartProducts, selection.cartProducts);
    Object.assign(result.favoriteProducts, selection.favoriteProducts);
    for (const [id, qty] of Object.entries(selection.cart)) {
      result.cart[id] = Math.min((result.cart[id] ?? 0) + qty, stockLimit(result.cartProducts[id]));
    }
    result.favorites = [...new Set([...result.favorites, ...selection.favorites])];
  }
  return result;
}
