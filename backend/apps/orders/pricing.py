from decimal import ROUND_HALF_UP, Decimal

from rest_framework.exceptions import ValidationError

FIXED_CITY_DELIVERY_FEE_UZS = Decimal('30000')
OUTER_CITY_DELIVERY_FEE_UZS = Decimal('45000')
FREE_DELIVERY_MIN_AMOUNT_UZS = Decimal('500000')
UZS_PER_PRICE_UNIT = Decimal('12650')
MONEY_QUANT = Decimal('0.01')


def uzs_to_price_units(amount: Decimal) -> Decimal:
    return (amount / UZS_PER_PRICE_UNIT).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


FIXED_CITY_DELIVERY_FEE = uzs_to_price_units(FIXED_CITY_DELIVERY_FEE_UZS)
OUTER_CITY_DELIVERY_FEE = uzs_to_price_units(OUTER_CITY_DELIVERY_FEE_UZS)
FREE_DELIVERY_MIN_AMOUNT = uzs_to_price_units(FREE_DELIVERY_MIN_AMOUNT_UZS)


def calculate_delivery_fee(subtotal: Decimal, delivery_zone=None) -> Decimal:
    city = getattr(delivery_zone, 'city', None)
    free_threshold = getattr(city, 'free_delivery_threshold', FREE_DELIVERY_MIN_AMOUNT)
    default_fee = getattr(city, 'default_delivery_fee', FIXED_CITY_DELIVERY_FEE)
    zone_fee = getattr(delivery_zone, 'fee', None)
    if free_threshold < 0 or default_fee < 0 or (zone_fee is not None and zone_fee < 0):
        raise ValidationError({'delivery_zone_id': 'Delivery fee settings must not be negative.'})

    if subtotal >= free_threshold:
        return Decimal('0.00')
    if delivery_zone is not None:
        return zone_fee
    return default_fee
