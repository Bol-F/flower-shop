from decimal import Decimal, ROUND_HALF_UP


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
    if subtotal >= FREE_DELIVERY_MIN_AMOUNT:
        return Decimal('0.00')
    if delivery_zone is not None:
        return delivery_zone.fee
    return FIXED_CITY_DELIVERY_FEE
