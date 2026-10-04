import type { Currency } from "./types";

/** Default used only for bundled demo data; live checkout reads the API rate. */
export const UZS_PER_USD = 12650;

export function toUzs(usd: number, rate = UZS_PER_USD): number {
  return Math.round(usd * rate * 100) / 100;
}

export function formatPrice(usd: number, currency: Currency, rate = UZS_PER_USD): string {
  if (currency === "UZS") {
    return `${toUzs(usd, rate).toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 2 }).replace(/,/g, " ")} so'm`;
  }
  return `$${usd.toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`;
}
