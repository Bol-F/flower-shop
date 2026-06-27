import { UZS_PER_USD } from "./currency";

export const FIXED_CITY_DELIVERY_FEE_UZS = 30000;
export const FREE_DELIVERY_MIN_AMOUNT_UZS = 500000;

function roundMoney(value: number): number {
  return Math.round(value * 100) / 100;
}

export const FIXED_CITY_DELIVERY_FEE = roundMoney(
  FIXED_CITY_DELIVERY_FEE_UZS / UZS_PER_USD,
);
export const FREE_DELIVERY_MIN_AMOUNT = roundMoney(
  FREE_DELIVERY_MIN_AMOUNT_UZS / UZS_PER_USD,
);

export const deliveryTimeSlots = [
  "09:00-12:00",
  "12:00-15:00",
  "15:00-18:00",
  "18:00-21:00",
] as const;

export type DeliveryTimeSlot = (typeof deliveryTimeSlots)[number];

export function calculateDeliveryFee(subtotal: number): number {
  return subtotal >= FREE_DELIVERY_MIN_AMOUNT ? 0 : FIXED_CITY_DELIVERY_FEE;
}
