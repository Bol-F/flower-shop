import { expect, it } from "vitest";
import { calculateDeliveryFee, FREE_DELIVERY_MIN_AMOUNT } from "./delivery";

it("uses the city's configured free-delivery threshold", () => {
  const zone = { fee: 5, freeDeliveryThreshold: 100 };
  expect(calculateDeliveryFee(60, zone)).toBe(5);
  expect(calculateDeliveryFee(100, zone)).toBe(0);
});

it("supports free delivery configured for every order", () => {
  expect(calculateDeliveryFee(10, { fee: 5, freeDeliveryThreshold: 0 })).toBe(0);
});

it("retains default delivery pricing when no city threshold is supplied", () => {
  expect(calculateDeliveryFee(10, { fee: 3 })).toBe(3);
  expect(calculateDeliveryFee(FREE_DELIVERY_MIN_AMOUNT, { fee: 3 })).toBe(0);
});
