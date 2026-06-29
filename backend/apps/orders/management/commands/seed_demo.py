from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from apps.categories.models import Category
from apps.contact.models import UserMessage
from apps.marketplace.models import City, Courier, PromoCode, Vendor
from apps.orders.models import DeliveryZone, Order, OrderItem
from apps.products.models import Product
from apps.reviews.models import Review


DEMO_PASSWORD = 'demo12345'


CATEGORIES = [
    {
        'name': 'Roses',
        'description': 'Classic rose bouquets for romance, anniversaries, and celebrations.',
    },
    {
        'name': 'Lilies',
        'description': 'Elegant lily arrangements with a clean, graceful style.',
    },
    {
        'name': 'Tulips',
        'description': 'Bright seasonal tulips for fresh spring gifts.',
    },
    {
        'name': 'Flower Boxes',
        'description': 'Modern boxed arrangements ready for birthdays and events.',
    },
    {
        'name': 'Premium Gifts',
        'description': 'Luxury orchids, baskets, and statement floral gifts.',
    },
    {
        'name': 'Wedding Flowers',
        'description': 'Soft bridal bouquets and event-ready arrangements.',
    },
    {
        'name': 'Sunflowers',
        'description': 'Warm sunflower bouquets for cheerful everyday gifting.',
    },
]


PRODUCTS = [
    {
        'name': 'Red Rose Bouquet',
        'category': 'Roses',
        'description': 'Twelve red roses with eucalyptus, wrapped in matte paper.',
        'price': Decimal('45.00'),
        'stock': 24,
        'low_stock_threshold': 5,
        'is_available': True,
        'color': '#b91c1c',
    },
    {
        'name': 'White Lily Bouquet',
        'category': 'Lilies',
        'description': 'White lilies with seasonal greens for a calm, elegant gift.',
        'price': Decimal('52.00'),
        'stock': 16,
        'low_stock_threshold': 4,
        'is_available': True,
        'color': '#f8fafc',
    },
    {
        'name': 'Tulip Spring Mix',
        'category': 'Tulips',
        'description': 'A colorful mixed tulip bouquet with fresh spring tones.',
        'price': Decimal('38.00'),
        'stock': 30,
        'low_stock_threshold': 6,
        'is_available': True,
        'color': '#f97316',
    },
    {
        'name': 'Birthday Flower Box',
        'category': 'Flower Boxes',
        'description': 'A bright boxed arrangement designed for birthday delivery.',
        'price': Decimal('64.00'),
        'stock': 12,
        'low_stock_threshold': 3,
        'is_available': True,
        'color': '#ec4899',
    },
    {
        'name': 'Romantic Pink Roses',
        'category': 'Roses',
        'description': 'Soft pink roses with delicate fillers for romantic occasions.',
        'price': Decimal('48.00'),
        'stock': 2,
        'low_stock_threshold': 4,
        'is_available': True,
        'color': '#f9a8d4',
    },
    {
        'name': 'Premium Orchid Basket',
        'category': 'Premium Gifts',
        'description': 'A premium orchid basket for a long-lasting elegant gift.',
        'price': Decimal('95.00'),
        'stock': 1,
        'low_stock_threshold': 3,
        'is_available': True,
        'color': '#7c3aed',
    },
    {
        'name': 'Wedding Bouquet',
        'category': 'Wedding Flowers',
        'description': 'A soft white and blush bouquet designed for wedding styling.',
        'price': Decimal('120.00'),
        'stock': 0,
        'low_stock_threshold': 2,
        'is_available': True,
        'color': '#fde68a',
    },
    {
        'name': 'Sunflower Joy Bouquet',
        'category': 'Sunflowers',
        'description': 'Sunflowers and greenery wrapped for a cheerful delivery.',
        'price': Decimal('42.00'),
        'stock': 20,
        'low_stock_threshold': 5,
        'is_available': True,
        'color': '#eab308',
    },
]


DELIVERY_ZONES = [
    {
        'name': 'Tashkent Center',
        'fee': Decimal('2.37'),
        'description': 'Central Tashkent delivery zone.',
        'requires_manual_confirmation': False,
    },
    {
        'name': 'Outer Tashkent',
        'fee': Decimal('3.56'),
        'description': 'Outer Tashkent neighborhoods.',
        'requires_manual_confirmation': False,
    },
    {
        'name': 'Outside City',
        'fee': Decimal('0.00'),
        'description': 'Manual confirmation required before delivery.',
        'requires_manual_confirmation': True,
    },
]


PROMO_CODES = [
    {
        'code': 'DEMO10',
        'discount_type': PromoCode.DiscountType.PERCENT,
        'discount_value': Decimal('10.00'),
        'min_order_amount': Decimal('30.00'),
        'max_discount_amount': Decimal('15.00'),
    },
    {
        'code': 'BLOOM5',
        'discount_type': PromoCode.DiscountType.FIXED_AMOUNT,
        'discount_value': Decimal('5.00'),
        'min_order_amount': Decimal('25.00'),
        'max_discount_amount': None,
    },
]


class Command(BaseCommand):
    help = 'Seed safe demo users, products, orders, reviews, and support data.'

    def handle(self, *args, **options):
        with transaction.atomic():
            customer = self._upsert_user(
                email='customer@example.com',
                username='customer',
                first_name='Demo',
                last_name='Customer',
                is_staff=False,
            )
            staff = self._upsert_user(
                email='staff@example.com',
                username='staff',
                first_name='Demo',
                last_name='Staff',
                is_staff=True,
            )
            city = self._upsert_city()
            vendor = self._upsert_vendor(city)
            courier = self._upsert_courier(staff, city)
            categories = self._upsert_categories()
            products = self._upsert_products(categories, city, vendor)
            zones = self._upsert_delivery_zones(city)
            promos = self._upsert_promo_codes()

            self._upsert_reviews(customer, products)
            self._upsert_support_messages(customer)
            orders = self._upsert_orders(
                customer, city, vendor, courier, zones, promos, products
            )
            self._sync_promo_usage(promos)

        self.stdout.write(self.style.SUCCESS('Demo data is ready.'))
        self.stdout.write(f'  Customer: customer@example.com / {DEMO_PASSWORD}')
        self.stdout.write(f'  Staff:    staff@example.com / {DEMO_PASSWORD}')
        self.stdout.write(f'  Products: {len(products)}')
        self.stdout.write(f'  Orders:   {len(orders)} demo orders')

    def _upsert_user(self, *, email, username, first_name, last_name, is_staff):
        User = get_user_model()
        safe_username = self._available_username(User, username, email)
        user, _ = User.objects.update_or_create(
            email=email,
            defaults={
                'username': safe_username,
                'first_name': first_name,
                'last_name': last_name,
                'phone': '+998901234567' if not is_staff else '+998901112233',
                'address': 'Demo address, Tashkent',
                'city': 'Tashkent',
                'language': User.Language.EN,
                'currency': User.Currency.UZS,
                'is_staff': is_staff,
                'is_superuser': False,
                'is_active': True,
            },
        )
        user.set_password(DEMO_PASSWORD)
        user.save(update_fields=['password'])
        return user

    def _available_username(self, User, username, email):
        conflict = User.objects.filter(username=username).exclude(email=email).exists()
        return f'{username}_demo' if conflict else username

    def _upsert_city(self):
        city, _ = City.objects.update_or_create(
            slug='tashkent',
            defaults={
                'name': 'Tashkent',
                'country': 'Uzbekistan',
                'currency': City.Currency.UZS,
                'is_active': True,
                'default_delivery_fee': Decimal('2.37'),
                'free_delivery_threshold': Decimal('39.53'),
            },
        )
        return city

    def _upsert_vendor(self, city):
        vendor, _ = Vendor.objects.update_or_create(
            slug='bloom-petal-demo-florist',
            defaults={
                'name': 'Bloom & Petal Demo Florist',
                'phone': '+998901000000',
                'address': 'Demo florist studio, Tashkent',
                'city': city,
                'is_active': True,
                'commission_percent': Decimal('10.00'),
            },
        )
        return vendor

    def _upsert_courier(self, user, city):
        courier, _ = Courier.objects.update_or_create(
            user=user,
            defaults={
                'phone': '+998901112233',
                'city': city,
                'is_active': True,
                'current_status': Courier.Status.AVAILABLE,
            },
        )
        return courier

    def _upsert_categories(self):
        categories = {}
        for data in CATEGORIES:
            category, _ = Category.objects.update_or_create(
                name=data['name'],
                defaults={'description': data['description']},
            )
            categories[data['name']] = category
        return categories

    def _upsert_products(self, categories, city, vendor):
        products = {}
        for data in PRODUCTS:
            slug = slugify(data['name'])
            image_path = self._write_placeholder_svg(slug, data['name'], data['color'])
            product, _ = Product.objects.update_or_create(
                slug=slug,
                defaults={
                    'name': data['name'],
                    'description': data['description'],
                    'price': data['price'],
                    'category': categories[data['category']],
                    'city': city,
                    'vendor': vendor,
                    'image': image_path,
                    'stock': data['stock'],
                    'low_stock_threshold': data['low_stock_threshold'],
                    'is_available': data['is_available'],
                },
            )
            products[data['name']] = product
        return products

    def _write_placeholder_svg(self, slug, title, color):
        relative_path = Path('products') / 'demo' / f'{slug}.svg'
        output_path = Path(settings.MEDIA_ROOT) / relative_path
        output_path.parent.mkdir(parents=True, exist_ok=True)

        safe_title = (
            title.replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
        )
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="900" viewBox="0 0 1200 900">
  <rect width="1200" height="900" fill="#f8fafc"/>
  <circle cx="600" cy="385" r="210" fill="{color}" opacity="0.9"/>
  <circle cx="470" cy="330" r="120" fill="#ffffff" opacity="0.42"/>
  <circle cx="730" cy="330" r="120" fill="#ffffff" opacity="0.28"/>
  <rect x="0" y="680" width="1200" height="220" fill="#111827"/>
  <text x="600" y="770" text-anchor="middle" font-family="Arial, sans-serif" font-size="54" font-weight="700" fill="#ffffff">{safe_title}</text>
  <text x="600" y="830" text-anchor="middle" font-family="Arial, sans-serif" font-size="28" fill="#d1d5db">Bloom &amp; Petal demo image</text>
</svg>
'''
        output_path.write_text(svg, encoding='utf-8')
        return str(relative_path).replace('\\', '/')

    def _upsert_delivery_zones(self, city):
        zones = {}
        for data in DELIVERY_ZONES:
            zone, _ = DeliveryZone.objects.update_or_create(
                name=data['name'],
                defaults={
                    'city': city,
                    'fee': data['fee'],
                    'is_active': True,
                    'requires_manual_confirmation': data['requires_manual_confirmation'],
                    'description': data['description'],
                },
            )
            zones[data['name']] = zone
        return zones

    def _upsert_promo_codes(self):
        promos = {}
        now = timezone.now()
        for data in PROMO_CODES:
            promo, _ = PromoCode.objects.update_or_create(
                code=data['code'],
                defaults={
                    'discount_type': data['discount_type'],
                    'discount_value': data['discount_value'],
                    'min_order_amount': data['min_order_amount'],
                    'max_discount_amount': data['max_discount_amount'],
                    'is_active': True,
                    'valid_from': now - timedelta(days=1),
                    'valid_until': now + timedelta(days=365),
                    'usage_limit': None,
                },
            )
            promos[data['code']] = promo
        return promos

    def _upsert_reviews(self, customer, products):
        reviews = [
            ('Red Rose Bouquet', 5, 'Beautiful roses and the delivery was right on time.'),
            ('Birthday Flower Box', 5, 'The birthday box looked premium and fresh.'),
            ('Sunflower Joy Bouquet', 4, 'Bright and cheerful, exactly like the photo.'),
        ]
        for product_name, rating, body in reviews:
            Review.objects.update_or_create(
                user=customer,
                product=products[product_name].slug,
                defaults={'rating': rating, 'body': body},
            )

    def _upsert_support_messages(self, customer):
        UserMessage.objects.update_or_create(
            user=customer,
            subject='Demo question about delivery',
            is_from_admin=False,
            defaults={
                'body': 'Can you deliver flowers during the evening time slot?',
                'is_read': False,
                'admin_reply': '',
                'replied_at': None,
            },
        )
        UserMessage.objects.update_or_create(
            user=customer,
            subject='Demo message with staff reply',
            is_from_admin=False,
            defaults={
                'body': 'I need help choosing flowers for a birthday.',
                'is_read': True,
                'admin_reply': 'We recommend the Birthday Flower Box for this occasion.',
                'replied_at': timezone.now() - timedelta(hours=3),
            },
        )

    def _upsert_orders(self, customer, city, vendor, courier, zones, promos, products):
        today = timezone.localdate()
        now = timezone.now()
        specs = [
            {
                'marker': 'Demo seed: pending cash order',
                'status': Order.Status.PENDING,
                'payment_method': Order.PaymentMethod.CASH,
                'payment_status': Order.PaymentStatus.UNPAID,
                'payment_provider': 'cash',
                'payment_reference': '',
                'zone': zones['Tashkent Center'],
                'delivery_date': today,
                'delivery_time_slot': Order.DeliveryTimeSlot.MIDDAY,
                'recipient_name': 'Ali Karimov',
                'recipient_phone': '+998901234001',
                'gift_note': 'Have a wonderful day!',
                'items': [('Red Rose Bouquet', 1), ('Sunflower Joy Bouquet', 1)],
                'promo': None,
            },
            {
                'marker': 'Demo seed: confirmed card order',
                'status': Order.Status.CONFIRMED,
                'payment_method': Order.PaymentMethod.CARD,
                'payment_status': Order.PaymentStatus.PENDING,
                'payment_provider': 'test',
                'payment_reference': 'DEMO-CARD-PENDING',
                'zone': zones['Outer Tashkent'],
                'delivery_date': today + timedelta(days=1),
                'delivery_time_slot': Order.DeliveryTimeSlot.AFTERNOON,
                'recipient_name': 'Madina Yusufova',
                'recipient_phone': '+998901234002',
                'gift_note': 'Congratulations on your new home.',
                'items': [('White Lily Bouquet', 1)],
                'promo': promos['BLOOM5'],
            },
            {
                'marker': 'Demo seed: preparing online paid order',
                'status': Order.Status.PREPARING,
                'payment_method': Order.PaymentMethod.ONLINE,
                'payment_status': Order.PaymentStatus.PAID,
                'payment_provider': 'test',
                'payment_reference': 'DEMO-ONLINE-PAID',
                'zone': zones['Tashkent Center'],
                'delivery_date': today + timedelta(days=1),
                'delivery_time_slot': Order.DeliveryTimeSlot.MORNING,
                'recipient_name': 'Nodira Akhmedova',
                'recipient_phone': '+998901234003',
                'gift_note': 'Happy birthday!',
                'items': [('Birthday Flower Box', 1), ('Tulip Spring Mix', 1)],
                'promo': promos['DEMO10'],
            },
            {
                'marker': 'Demo seed: courier picked up card order',
                'status': Order.Status.COURIER_PICKED_UP,
                'payment_method': Order.PaymentMethod.CARD,
                'payment_status': Order.PaymentStatus.PAID,
                'payment_provider': 'test',
                'payment_reference': 'DEMO-CARD-PAID',
                'zone': zones['Outer Tashkent'],
                'delivery_date': today,
                'delivery_time_slot': Order.DeliveryTimeSlot.EVENING,
                'recipient_name': 'Sardor Rahimov',
                'recipient_phone': '+998901234004',
                'gift_note': 'Thinking of you.',
                'items': [('Romantic Pink Roses', 1)],
                'promo': None,
                'assigned_courier': courier,
                'courier_assigned_at': now - timedelta(hours=2),
                'courier_picked_up_at': now - timedelta(minutes=25),
            },
            {
                'marker': 'Demo seed: delivered cash paid order',
                'status': Order.Status.DELIVERED,
                'payment_method': Order.PaymentMethod.CASH,
                'payment_status': Order.PaymentStatus.PAID,
                'payment_provider': 'manual',
                'payment_reference': 'DEMO-CASH-MANUAL',
                'zone': zones['Tashkent Center'],
                'delivery_date': today - timedelta(days=1),
                'delivery_time_slot': Order.DeliveryTimeSlot.MIDDAY,
                'recipient_name': 'Zarina Saidova',
                'recipient_phone': '+998901234005',
                'gift_note': 'Thank you!',
                'items': [('Premium Orchid Basket', 1)],
                'promo': None,
                'assigned_courier': courier,
                'courier_assigned_at': now - timedelta(days=1, hours=4),
                'courier_picked_up_at': now - timedelta(days=1, hours=2),
                'delivered_at': now - timedelta(days=1, hours=1),
                'loyalty_points_earned': 9,
            },
            {
                'marker': 'Demo seed: failed online payment order',
                'status': Order.Status.PENDING,
                'payment_method': Order.PaymentMethod.ONLINE,
                'payment_status': Order.PaymentStatus.FAILED,
                'payment_provider': 'test',
                'payment_reference': 'DEMO-ONLINE-FAILED',
                'zone': zones['Outside City'],
                'delivery_date': today + timedelta(days=2),
                'delivery_time_slot': Order.DeliveryTimeSlot.AFTERNOON,
                'recipient_name': 'Bekzod Karimov',
                'recipient_phone': '+998901234006',
                'gift_note': 'Please call before delivery.',
                'items': [('Wedding Bouquet', 1)],
                'promo': None,
            },
        ]

        orders = []
        for spec in specs:
            order = self._upsert_order(customer, city, vendor, products, spec)
            orders.append(order)
        return orders

    def _upsert_order(self, customer, city, vendor, products, spec):
        subtotal = sum(
            products[product_name].price * quantity
            for product_name, quantity in spec['items']
        )
        delivery_fee = spec['zone'].fee
        discount = self._calculate_discount(spec.get('promo'), subtotal)
        total = max(subtotal + delivery_fee - discount, Decimal('0.00'))
        paid_at = (
            timezone.now() - timedelta(hours=4)
            if spec['payment_status'] == Order.PaymentStatus.PAID
            else None
        )

        defaults = {
            'city': city,
            'vendor': vendor,
            'assigned_courier': spec.get('assigned_courier'),
            'status': spec['status'],
            'total_price': total,
            'shipping_address': 'Demo delivery address, Tashkent',
            'phone': '+998901234000',
            'payment_method': spec['payment_method'],
            'payment_status': spec['payment_status'],
            'payment_provider': spec['payment_provider'],
            'payment_reference': spec['payment_reference'],
            'paid_at': paid_at,
            'promo_code': spec.get('promo'),
            'discount_amount': discount,
            'delivery_address': f'{spec["zone"].name}, Tashkent',
            'delivery_lat': Decimal('41.311081'),
            'delivery_lng': Decimal('69.240562'),
            'delivery_date': spec['delivery_date'],
            'delivery_time_slot': spec['delivery_time_slot'],
            'delivery_zone': spec['zone'],
            'delivery_requires_confirmation': spec['zone'].requires_manual_confirmation,
            'courier_assigned_at': spec.get('courier_assigned_at'),
            'courier_picked_up_at': spec.get('courier_picked_up_at'),
            'delivered_at': spec.get('delivered_at'),
            'recipient_name': spec['recipient_name'],
            'recipient_phone': spec['recipient_phone'],
            'gift_note': spec['gift_note'],
            'call_recipient_before_delivery': True,
            'delivery_fee': delivery_fee,
            'loyalty_points_earned': spec.get('loyalty_points_earned', 0),
        }
        order, _ = Order.objects.update_or_create(
            user=customer,
            notes=spec['marker'],
            defaults=defaults,
        )
        self._replace_order_items(order, products, spec['items'])
        return order

    def _replace_order_items(self, order, products, items):
        order.items.all().delete()
        OrderItem.objects.bulk_create(
            [
                OrderItem(
                    order=order,
                    product=products[product_name],
                    product_name=product_name,
                    product_price=products[product_name].price,
                    quantity=quantity,
                )
                for product_name, quantity in items
            ]
        )

    def _calculate_discount(self, promo, subtotal):
        if not promo:
            return Decimal('0.00')
        if promo.discount_type == PromoCode.DiscountType.FIXED_AMOUNT:
            return min(promo.discount_value, subtotal)
        discount = subtotal * promo.discount_value / Decimal('100')
        if promo.max_discount_amount is not None:
            discount = min(discount, promo.max_discount_amount)
        return discount.quantize(Decimal('0.01'))

    def _sync_promo_usage(self, promos):
        for promo in promos.values():
            PromoCode.objects.filter(pk=promo.pk).update(
                used_count=Order.objects.filter(promo_code=promo).count()
            )
