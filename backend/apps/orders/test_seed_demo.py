from io import StringIO

import pytest
from django.core.management import call_command
from django.test import override_settings

from apps.contact.models import UserMessage
from apps.marketplace.models import PromoCode
from apps.orders.models import Order
from apps.products.models import Product
from apps.reviews.models import Review
from apps.users.models import User


@pytest.mark.django_db
def test_seed_demo_runs_idempotently(tmp_path):
    with override_settings(MEDIA_ROOT=tmp_path):
        call_command('seed_demo', stdout=StringIO())
        first_counts = {
            'users': User.objects.filter(
                email__in=['customer@example.com', 'staff@example.com']
            ).count(),
            'products': Product.objects.filter(
                slug__in=[
                    'red-rose-bouquet',
                    'white-lily-bouquet',
                    'tulip-spring-mix',
                    'birthday-flower-box',
                    'romantic-pink-roses',
                    'premium-orchid-basket',
                    'wedding-bouquet',
                    'sunflower-joy-bouquet',
                ]
            ).count(),
            'orders': Order.objects.filter(notes__startswith='Demo seed:').count(),
            'reviews': Review.objects.count(),
            'messages': UserMessage.objects.count(),
            'promos': PromoCode.objects.filter(code__in=['DEMO10', 'BLOOM5']).count(),
        }
        demo_products = Product.objects.filter(
            slug__in=[
                'red-rose-bouquet',
                'white-lily-bouquet',
                'tulip-spring-mix',
                'birthday-flower-box',
                'romantic-pink-roses',
                'premium-orchid-basket',
                'wedding-bouquet',
                'sunflower-joy-bouquet',
            ]
        )
        first_image_names = {product.slug: product.image.name for product in demo_products}
        for product in demo_products:
            image_path = tmp_path / product.image.name
            assert product.image.name.endswith('-v2.webp')
            assert image_path.is_file()
            image_bytes = image_path.read_bytes()
            assert image_bytes[:4] == b'RIFF'
            assert image_bytes[8:12] == b'WEBP'

        call_command('seed_demo', stdout=StringIO())
        second_counts = {
            'users': User.objects.filter(
                email__in=['customer@example.com', 'staff@example.com']
            ).count(),
            'products': Product.objects.filter(
                slug__in=[
                    'red-rose-bouquet',
                    'white-lily-bouquet',
                    'tulip-spring-mix',
                    'birthday-flower-box',
                    'romantic-pink-roses',
                    'premium-orchid-basket',
                    'wedding-bouquet',
                    'sunflower-joy-bouquet',
                ]
            ).count(),
            'orders': Order.objects.filter(notes__startswith='Demo seed:').count(),
            'reviews': Review.objects.count(),
            'messages': UserMessage.objects.count(),
            'promos': PromoCode.objects.filter(code__in=['DEMO10', 'BLOOM5']).count(),
        }
        second_image_names = {
            product.slug: product.image.name
            for product in Product.objects.filter(slug__in=first_image_names)
        }

    assert first_counts == {
        'users': 2,
        'products': 8,
        'orders': 6,
        'reviews': 3,
        'messages': 2,
        'promos': 2,
    }
    assert second_counts == first_counts
    assert second_image_names == first_image_names
    assert User.objects.get(email='customer@example.com').check_password('demo12345')
    staff = User.objects.get(email='staff@example.com')
    assert staff.check_password('demo12345')
    assert staff.is_staff is True
    assert staff.is_superuser is False
    assert staff.has_perm('orders.view_order')
    assert staff.has_perm('orders.change_order')
    assert staff.has_perm('products.view_product')
    assert staff.has_perm('contact.view_usermessage')
    assert Product.objects.get(slug='romantic-pink-roses').stock_status == 'low_stock'
    assert Product.objects.get(slug='wedding-bouquet').stock_status == 'out_of_stock'
    assert Order.objects.filter(notes__startswith='Demo seed:').count() == 6
