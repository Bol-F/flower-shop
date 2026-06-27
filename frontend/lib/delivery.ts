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

export interface DeliveryZoneOption {
  id: number;
  name: string;
  fee: number;
  requiresManualConfirmation: boolean;
  description: string;
}

export const fallbackDeliveryZones: DeliveryZoneOption[] = [
  {
    id: 0,
    name: "Tashkent Center",
    fee: FIXED_CITY_DELIVERY_FEE,
    requiresManualConfirmation: false,
    description: "Central Tashkent delivery.",
  },
  {
    id: -1,
    name: "Outer Tashkent",
    fee: roundMoney(45000 / UZS_PER_USD),
    requiresManualConfirmation: false,
    description: "Outer city delivery.",
  },
  {
    id: -2,
    name: "Outside City",
    fee: 0,
    requiresManualConfirmation: true,
    description: "Staff will confirm delivery availability and final fee.",
  },
];

export const deliveryTimeSlots = [
  "09:00-12:00",
  "12:00-15:00",
  "15:00-18:00",
  "18:00-21:00",
] as const;

export type DeliveryTimeSlot = (typeof deliveryTimeSlots)[number];

export function calculateDeliveryFee(
  subtotal: number,
  zone?: Pick<DeliveryZoneOption, "fee"> | null,
): number {
  if (subtotal >= FREE_DELIVERY_MIN_AMOUNT) return 0;
  return zone?.fee ?? FIXED_CITY_DELIVERY_FEE;
}
