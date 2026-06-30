from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.cart.services import add_item_to_cart
from apps.cart.serializers import CartSerializer
from apps.cart.services import get_cart_for_response
from apps.orders.models import Order

from .models import City, PromoCode

MONEY_QUANT = Decimal('0.01')


def get_default_city() -> City | None:
    return City.objects.filter(slug='tashkent', is_active=True).first()


def resolve_city(city_slug: str | None, user=None) -> City | None:
    if city_slug:
        city = City.objects.filter(slug=city_slug, is_active=True).first()
        if not city:
            raise ValidationError({'city': 'Selected city is not available.'})
        return city

    user_city = getattr(user, 'city', '') if user else ''
    if user_city:
        city = City.objects.filter(name__iexact=user_city, is_active=True).first()
        if city:
            return city

    return get_default_city()


def calculate_promo_discount(promo: PromoCode, subtotal: Decimal) -> Decimal:
    if promo.discount_type == PromoCode.DiscountType.FIXED_AMOUNT:
        discount = promo.discount_value
    else:
        discount = subtotal * promo.discount_value / Decimal('100')

    if promo.max_discount_amount is not None:
        discount = min(discount, promo.max_discount_amount)

    discount = min(discount, subtotal)
    return discount.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def validate_promo_code(code: str | None, subtotal: Decimal) -> tuple[PromoCode | None, Decimal]:
    if not code:
        return None, Decimal('0.00')

    normalized = code.strip().upper()
    try:
        promo = PromoCode.objects.get(code=normalized)
    except PromoCode.DoesNotExist:
        raise ValidationError({'promo_code': 'Promo code was not found.'})

    now = timezone.now()
    if not promo.is_active:
        raise ValidationError({'promo_code': 'Promo code is not active.'})
    if promo.valid_from and promo.valid_from > now:
        raise ValidationError({'promo_code': 'Promo code is not active yet.'})
    if promo.valid_until and promo.valid_until < now:
        raise ValidationError({'promo_code': 'Promo code has expired.'})
    if promo.usage_limit is not None and promo.used_count >= promo.usage_limit:
        raise ValidationError({'promo_code': 'Promo code usage limit reached.'})
    if subtotal < promo.min_order_amount:
        raise ValidationError({'promo_code': 'Order subtotal is below promo minimum.'})

    return promo, calculate_promo_discount(promo, subtotal)


def mark_promo_used(promo: PromoCode | None) -> None:
    if not promo:
        return
    updated = (
        PromoCode.objects
        .filter(pk=promo.pk)
        .filter(Q(usage_limit__isnull=True) | Q(used_count__lt=F('usage_limit')))
        .update(used_count=F('used_count') + 1)
    )
    if not updated:
        raise ValidationError({'promo_code': 'Promo code usage limit reached.'})


def award_loyalty_points_if_eligible(order: Order) -> Order:
    if (
        order.status != Order.Status.DELIVERED
        or order.payment_status not in [Order.PaymentStatus.PAID, Order.PaymentStatus.UNPAID]
        or order.loyalty_points_earned
    ):
        return order

    points = max(int(order.total_price), 1)
    user = order.user
    user.loyalty_points += points
    user.save(update_fields=['loyalty_points'])
    order.loyalty_points_earned = points
    order.save(update_fields=['loyalty_points_earned', 'updated_at'])
    return order


@transaction.atomic
def repeat_order_to_cart(order: Order, user) -> dict:
    if order.user_id != user.id and not user.is_staff:
        raise ValidationError('You cannot repeat this order.')

    added = []
    skipped = []
    for item in order.items.select_related('product'):
        product = item.product
        if not product or not product.is_available or product.stock <= 0:
            skipped.append(item.product_name)
            continue
        quantity = min(item.quantity, product.stock)
        add_item_to_cart(user, product.id, quantity)
        added.append({'product': product.name, 'quantity': quantity})

    return {
        'cart': CartSerializer(get_cart_for_response(user)).data,
        'added': added,
        'skipped': skipped,
    }
