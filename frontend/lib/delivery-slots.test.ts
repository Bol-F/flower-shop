import { afterEach, describe, expect, it, vi } from "vitest";
import { deliveryTimeSlots } from "./delivery";
import {
  availableDeliverySlots,
  defaultDeliverySelection,
  deliveryDateFromNow,
} from "./delivery-slots";

afterEach(() => vi.unstubAllEnvs());

describe("Tashkent delivery windows", () => {
  it.each([
    ["09:00-12:00", "12:00"],
    ["12:00-15:00", "15:00"],
    ["15:00-18:00", "18:00"],
    ["18:00-21:00", "21:00"],
  ] as const)("keeps %s available until its end and removes it exactly at %s", (slot, end) => {
    const cutoff = new Date(`2026-11-16T${end}:00+05:00`);
    expect(availableDeliverySlots("2026-11-16", new Date(cutoff.getTime() - 1))).toContain(slot);
    expect(availableDeliverySlots("2026-11-16", cutoff)).not.toContain(slot);
  });

  it("defaults to an available window and then tomorrow after the final end", () => {
    expect(defaultDeliverySelection(new Date("2026-11-16T15:00:00+05:00"))).toEqual({
      day: "today",
      date: "2026-11-16",
      slot: "15:00-18:00",
    });
    expect(defaultDeliverySelection(new Date("2026-11-16T21:00:00+05:00"))).toEqual({
      day: "tomorrow",
      date: "2026-11-17",
      slot: "12:00-15:00",
    });
  });

  it("keeps future-date windows available and rejects past dates", () => {
    const now = new Date("2026-11-16T23:59:00+05:00");
    expect(availableDeliverySlots("2026-11-17", now)).toEqual(deliveryTimeSlots);
    expect(availableDeliverySlots("2026-11-15", now)).toEqual([]);
  });

  it.each(["America/Los_Angeles", "Pacific/Kiritimati"])(
    "uses the shop's calendar independently of the device timezone %s",
    (deviceTimezone) => {
      vi.stubEnv("TZ", deviceTimezone);
      const now = new Date("2026-11-16T20:30:00Z");
      expect(deliveryDateFromNow(0, now)).toBe("2026-11-17");
      expect(deliveryDateFromNow(1, now)).toBe("2026-11-18");
      expect(availableDeliverySlots("2026-11-16", now)).toEqual([]);
    },
  );

  it("advances the shop calendar correctly across year boundaries", () => {
    expect(defaultDeliverySelection(new Date("2026-12-31T21:00:00+05:00")).date).toBe("2027-01-01");
  });
});
