"""Existing delivery windows evaluated in the shop's local timezone."""

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.utils import timezone

from .models import Order

DELIVERY_TIME_ZONE = ZoneInfo('Asia/Tashkent')


def delivery_now(now=None):
    return timezone.localtime(now or timezone.now(), DELIVERY_TIME_ZONE)


def available_delivery_slots(delivery_date, *, now=None):
    current = delivery_now(now)
    if delivery_date < current.date():
        return []
    slots = []
    for slot, _label in Order.DeliveryTimeSlot.choices:
        window_end = datetime.combine(
            delivery_date,
            time.fromisoformat(slot.split('-')[1]),
            tzinfo=DELIVERY_TIME_ZONE,
        )
        if window_end > current:
            slots.append(slot)
    return slots


def default_delivery_selection(*, now=None):
    current = delivery_now(now)
    date = current.date()
    slots = available_delivery_slots(date, now=current)
    if not slots:
        date += timedelta(days=1)
        slots = available_delivery_slots(date, now=current)
    slot = Order.DeliveryTimeSlot.MIDDAY if Order.DeliveryTimeSlot.MIDDAY in slots else slots[0]
    return date, slot
