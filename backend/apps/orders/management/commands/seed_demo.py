from __future__ import annotations

import shutil
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from apps.categories.models import Category
from apps.marketplace.models import City, PromoCode, Vendor
from apps.orders.models import DeliveryZone, Order
from apps.products.models import Product

DEMO_ASSET_DIR = Path(__file__).with_name('demo_assets')


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
    },
    {
        'name': 'White Lily Bouquet',
        'category': 'Lilies',
        'description': 'White lilies with seasonal greens for a calm, elegant gift.',
        'price': Decimal('52.00'),
        'stock': 16,
        'low_stock_threshold': 4,
        'is_available': True,
    },
    {
        'name': 'Tulip Spring Mix',
        'category': 'Tulips',
        'description': 'A colorful mixed tulip bouquet with fresh spring tones.',
        'price': Decimal('38.00'),
        'stock': 30,
        'low_stock_threshold': 6,
        'is_available': True,
    },
    {
        'name': 'Birthday Flower Box',
        'category': 'Flower Boxes',
        'description': 'A bright boxed arrangement designed for birthday delivery.',
        'price': Decimal('64.00'),
        'stock': 12,
        'low_stock_threshold': 3,
        'is_available': True,
    },
    {
        'name': 'Romantic Pink Roses',
        'category': 'Roses',
        'description': 'Soft pink roses with delicate fillers for romantic occasions.',
        'price': Decimal('48.00'),
        'stock': 2,
        'low_stock_threshold': 4,
        'is_available': True,
    },
    {
        'name': 'Premium Orchid Basket',
        'category': 'Premium Gifts',
        'description': 'A premium orchid basket for a long-lasting elegant gift.',
        'price': Decimal('95.00'),
        'stock': 1,
        'low_stock_threshold': 3,
        'is_available': True,
    },
    {
        'name': 'Wedding Bouquet',
        'category': 'Wedding Flowers',
        'description': 'A soft white and blush bouquet designed for wedding styling.',
        'price': Decimal('120.00'),
        'stock': 0,
        'low_stock_threshold': 2,
        'is_available': True,
    },
    {
        'name': 'Sunflower Joy Bouquet',
        'category': 'Sunflowers',
        'description': 'Sunflowers and greenery wrapped for a cheerful delivery.',
        'price': Decimal('42.00'),
        'stock': 20,
        'low_stock_threshold': 5,
        'is_available': True,
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
    help = 'Seed the public demo catalog, delivery zones, and promotions without login accounts.'

    def handle(self, *args, **options):
        # Personal sample data and shared-password accounts must never be restored
        # by a public web service restart. Existing history is deliberately retained.
        with transaction.atomic():
            city = self._upsert_city()
            vendor = self._upsert_vendor(city)
            categories = self._upsert_categories()
            products = self._upsert_products(categories, city, vendor)
            self._upsert_delivery_zones(city)
            promos = self._upsert_promo_codes()
            self._sync_promo_usage(promos)

        self.stdout.write(self.style.SUCCESS('Demo catalog is ready.'))
        self.stdout.write(f'  Products: {len(products)}')

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
            image_path = self._install_demo_image(slug)
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

    def _install_demo_image(self, slug):
        filename = f'{slug}-v2.webp'
        source_path = DEMO_ASSET_DIR / filename
        if not source_path.is_file():
            raise FileNotFoundError(f'Missing demo product image: {source_path}')

        relative_path = Path('products') / 'demo' / filename
        output_path = Path(settings.MEDIA_ROOT) / relative_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_path, output_path)
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

    def _sync_promo_usage(self, promos):
        for promo in promos.values():
            PromoCode.objects.filter(pk=promo.pk).update(
                used_count=Order.objects.filter(promo_code=promo).count()
            )
