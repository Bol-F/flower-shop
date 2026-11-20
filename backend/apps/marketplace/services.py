from decimal import ROUND_HALF_UP, Decimal

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.cart.serializers import CartSerializer
from apps.cart.services import add_item_to_cart, get_cart_for_response, get_cart_for_update
from apps.orders.models import Order
from apps.products.models import Product

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
        discount = subtotal * promo.discount_value / Decimal(100)

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
    # Legacy rows or direct ORM writes may predate model/admin validation.
    # Never let malformed configuration increase a total or grant >100% off.
    if (
        promo.discount_type not in PromoCode.DiscountType.values
        or promo.discount_value <= 0
        or (
            promo.discount_type == PromoCode.DiscountType.PERCENT
            and promo.discount_value > Decimal(100)
        )
        or promo.min_order_amount < 0
        or (promo.max_discount_amount is not None and promo.max_discount_amount < 0)
        or (promo.valid_until and promo.valid_until <= promo.valid_from)
    ):
        raise ValidationError({'promo_code': 'Promo code configuration is invalid.'})
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
        PromoCode.objects.filter(pk=promo.pk)
        .filter(Q(usage_limit__isnull=True) | Q(used_count__lt=F('usage_limit')))
        .update(used_count=F('used_count') + 1)
    )
    if not updated:
        raise ValidationError({'promo_code': 'Promo code usage limit reached.'})


@transaction.atomic
def award_loyalty_points_if_eligible(order: Order) -> Order:
    # Fulfillment and admin callers may hold stale instances. Lock the durable
    # award marker so retries cannot credit the same delivery twice.
    persisted = Order.objects.select_for_update().get(pk=order.pk)
    order.loyalty_points_earned = persisted.loyalty_points_earned
    order.updated_at = persisted.updated_at
    user_field = Order._meta.get_field('user')
    if user_field.is_cached(order):
        user_field.delete_cached_value(order)
    if (
        persisted.status != Order.Status.DELIVERED
        or persisted.payment_status not in [Order.PaymentStatus.PAID, Order.PaymentStatus.UNPAID]
        or persisted.loyalty_points_earned
    ):
        return order

    points = max(int(persisted.total_price), 1)
    # Independent delivered orders must not overwrite the same user's balance.
    get_user_model().objects.filter(pk=persisted.user_id).update(
        loyalty_points=F('loyalty_points') + points
    )
    persisted.loyalty_points_earned = points
    persisted.save(update_fields=['loyalty_points_earned', 'updated_at'])
    order.loyalty_points_earned = points
    order.updated_at = persisted.updated_at
    return order


@transaction.atomic
def repeat_order_to_cart(order: Order, user) -> dict:
    if order.user_id != user.id and not user.is_staff:
        raise ValidationError('You cannot repeat this order.')

    cart = get_cart_for_update(user)
    quantities = dict(cart.items.values_list('product_id', 'quantity'))
    items = list(order.items.all())
    product_ids = {item.product_id for item in items if item.product_id}
    products = (
        Product.objects.select_for_update().filter(pk__in=product_ids).order_by('pk').in_bulk()
    )
    available_ids = set(
        Product.objects.storefront().filter(pk__in=product_ids).values_list('pk', flat=True)
    )
    added = []
    skipped = []
    for item in items:
        product = products.get(item.product_id)
        remaining = max(product.stock - quantities.get(product.pk, 0), 0) if product else 0
        if not product or product.pk not in available_ids or not remaining:
            skipped.append(item.product_name)
            continue
        quantity = min(item.quantity, remaining)
        add_item_to_cart(user, product.id, quantity)
        quantities[product.pk] = quantities.get(product.pk, 0) + quantity
        added.append({'product': product.name, 'quantity': quantity})

    return {
        'cart': CartSerializer(get_cart_for_response(user)).data,
        'added': added,
        'skipped': skipped,
    }
