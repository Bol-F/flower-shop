import { deliveryTimeSlots, type DeliveryTimeSlot } from "./delivery";

export const DELIVERY_TIME_ZONE = "Asia/Tashkent";

const deliveryClock = new Intl.DateTimeFormat("en-CA", {
  timeZone: DELIVERY_TIME_ZONE,
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23",
});

function shopClock(now: Date) {
  const parts = Object.fromEntries(
    deliveryClock.formatToParts(now).map((part) => [part.type, part.value]),
  );
  return {
    date: `${parts.year}-${parts.month}-${parts.day}`,
    minutes: Number(parts.hour) * 60 + Number(parts.minute),
  };
}

export function deliveryDateFromNow(days = 0, now = new Date()): string {
  const date = shopClock(now).date;
  if (days === 0) return date;
  const [year, month, day] = date.split("-").map(Number);
  return new Date(Date.UTC(year, month - 1, day + days)).toISOString().slice(0, 10);
}

export function availableDeliverySlots(date: string, now = new Date()): DeliveryTimeSlot[] {
  const clock = shopClock(now);
  if (!date || date < clock.date) return [];
  if (date > clock.date) return [...deliveryTimeSlots];
  return deliveryTimeSlots.filter((slot) => {
    const [hour, minute] = slot.split("-")[1].split(":").map(Number);
    return hour * 60 + minute > clock.minutes;
  });
}

export function preferredDeliverySlot(
  date: string,
  now = new Date(),
): DeliveryTimeSlot | undefined {
  const slots = availableDeliverySlots(date, now);
  return slots.includes("12:00-15:00") ? "12:00-15:00" : slots[0];
}

export function defaultDeliverySelection(now = new Date()) {
  let day: "today" | "tomorrow" = "today";
  let date = deliveryDateFromNow(0, now);
  if (availableDeliverySlots(date, now).length === 0) {
    day = "tomorrow";
    date = deliveryDateFromNow(1, now);
  }
  return { day, date, slot: preferredDeliverySlot(date, now)! };
}
