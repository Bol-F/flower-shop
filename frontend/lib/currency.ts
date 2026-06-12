import type { Currency } from "./types";

/** demo mid-market rate; a real app would fetch this from the backend */
export const UZS_PER_USD = 12650;

export function toUzs(usd: number): number {
  // round to a clean 1 000 so'm step like local shops do
  return Math.round((usd * UZS_PER_USD) / 1000) * 1000;
}

export function formatPrice(usd: number, currency: Currency): string {
  if (currency === "UZS") {
    return `${toUzs(usd).toLocaleString("en-US").replace(/,/g, " ")} so'm`;
  }
  return `$${usd.toLocaleString("en-US")}`;
}
