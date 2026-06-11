import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.users.models import User
from apps.categories.models import Category
from apps.products.models import Product
from apps.cart.models import Cart, CartItem
from apps.orders.models import Order


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username='orderuser',
        email='order@example.com',
        password='pass123',
    )


@pytest.fixture
def product(db):
    category = Category.objects.create(name='Tulips', slug='tulips')
    return Product.objects.create(
        name='Tulip Bouquet',
        description='Colorful tulips',
        price='19.99',
        category=category,
        stock=15,
        is_available=True,
    )


@pytest.fixture
def cart_with_item(db, user, product):
    cart = Cart.objects.create(user=user)
    CartItem.objects.create(cart=cart, product=product, quantity=2)
    return cart


@pytest.mark.django_db
class TestOrderCreation:
    def test_create_order_success(self, api_client, user, cart_with_item):
        api_client.force_authenticate(user=user)
        url = reverse('order-create')
        response = api_client.post(
            url,
            {
                'shipping_address': '123 Flower Street, Garden City',
                'phone': '+1234567890',
                'notes': 'Please handle with care',
            },
            format='json',
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert Order.objects.filter(user=user).count() == 1
        assert response.data['total_price'] == '39.98'

    def test_create_order_empty_cart(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse('order-create')
        response = api_client.post(
            url,
            {'shipping_address': '123 Street', 'phone': '+1234567890'},
            format='json',
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_order_list_returns_user_orders(self, api_client, user, cart_with_item):
        api_client.force_authenticate(user=user)
        api_client.post(
            reverse('order-create'),
            {'shipping_address': '123 Street', 'phone': '+1234567890'},
            format='json',
        )
        response = api_client.get(reverse('order-list'))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_order_requires_auth(self, api_client):
        response = api_client.post(reverse('order-create'), {})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
