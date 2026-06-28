from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.categories.models import Category
from apps.marketplace.models import City, PromoCode, WishlistItem
from apps.products.models import Product
from apps.users.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username='marketuser',
        email='market@example.com',
        password='pass123',
    )


@pytest.fixture
def product(db):
    category = Category.objects.create(name='Marketplace', slug='marketplace')
    return Product.objects.create(
        name='Marketplace Bouquet',
        description='Ready for wishlist',
        price='20.00',
        category=category,
        stock=5,
        is_available=True,
    )


@pytest.mark.django_db
class TestMarketplaceFoundation:
    def test_city_list_includes_default_tashkent(self, api_client):
        response = api_client.get(reverse('marketplace-city-list'))

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 1
        assert response.data['results'][0]['slug'] == 'tashkent'

    def test_validate_percent_promo_code(self, api_client):
        PromoCode.objects.create(
            code='spring10',
            discount_type=PromoCode.DiscountType.PERCENT,
            discount_value='10.00',
            min_order_amount='10.00',
            max_discount_amount='5.00',
            valid_from=timezone.now(),
        )

        response = api_client.post(
            reverse('promo-validate'),
            {'code': 'spring10', 'subtotal': '40.00'},
            format='json',
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['code'] == 'SPRING10'
        assert response.data['discount_amount'] == '4.00'

    def test_reject_promo_below_minimum(self, api_client):
        PromoCode.objects.create(
            code='BIGORDER',
            discount_type=PromoCode.DiscountType.FIXED_AMOUNT,
            discount_value='5.00',
            min_order_amount='50.00',
        )

        response = api_client.post(
            reverse('promo-validate'),
            {'code': 'BIGORDER', 'subtotal': '20.00'},
            format='json',
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_wishlist_add_list_remove(self, api_client, user, product):
        api_client.force_authenticate(user=user)

        add_response = api_client.post(
            reverse('wishlist'),
            {'product_id': product.id},
            format='json',
        )
        list_response = api_client.get(reverse('wishlist'))
        delete_response = api_client.delete(reverse('wishlist-delete', args=[product.id]))

        assert add_response.status_code == status.HTTP_201_CREATED
        assert list_response.status_code == status.HTTP_200_OK
        assert list_response.data['count'] == 1
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT
        assert not WishlistItem.objects.filter(user=user, product=product).exists()

    def test_city_defaults_are_base_price_units(self):
        city = City.objects.get(slug='tashkent')

        assert city.default_delivery_fee == Decimal('2.37')
        assert city.free_delivery_threshold == Decimal('39.53')
