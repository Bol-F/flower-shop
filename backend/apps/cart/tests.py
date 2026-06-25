import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.users.models import User
from apps.categories.models import Category
from apps.products.models import Product
from apps.cart.models import Cart


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username='cartuser',
        email='cart@example.com',
        password='pass123',
    )


@pytest.fixture
def product(db):
    category = Category.objects.create(name='Bouquets', slug='bouquets')
    return Product.objects.create(
        name='Spring Bouquet',
        description='Fresh spring flowers',
        price='24.99',
        category=category,
        stock=10,
        is_available=True,
    )


@pytest.mark.django_db
class TestCart:
    def test_cart_requires_auth(self, api_client):
        url = reverse('cart')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_empty_cart(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse('cart')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_items'] == 0

    def test_add_item_to_cart(self, api_client, user, product):
        api_client.force_authenticate(user=user)
        url = reverse('cart-items')
        response = api_client.post(
            url,
            {'product_id': product.id, 'quantity': 2},
            format='json',
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['total_items'] == 2

    def test_add_item_rejects_quantity_above_stock(self, api_client, user, product):
        api_client.force_authenticate(user=user)
        response = api_client.post(
            reverse('cart-items'),
            {'product_id': product.id, 'quantity': product.stock + 1},
            format='json',
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_cart_item(self, api_client, user, product):
        api_client.force_authenticate(user=user)
        api_client.post(
            reverse('cart-items'),
            {'product_id': product.id, 'quantity': 1},
            format='json',
        )
        url = reverse('cart-item-detail', kwargs={'product_id': product.id})
        response = api_client.patch(url, {'quantity': 3}, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_items'] == 3

    def test_update_cart_item_rejects_quantity_above_stock(self, api_client, user, product):
        api_client.force_authenticate(user=user)
        api_client.post(
            reverse('cart-items'),
            {'product_id': product.id, 'quantity': 1},
            format='json',
        )
        url = reverse('cart-item-detail', kwargs={'product_id': product.id})
        response = api_client.patch(
            url,
            {'quantity': product.stock + 1},
            format='json',
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_remove_item_from_cart(self, api_client, user, product):
        api_client.force_authenticate(user=user)
        api_client.post(
            reverse('cart-items'),
            {'product_id': product.id, 'quantity': 1},
            format='json',
        )
        url = reverse('cart-item-detail', kwargs={'product_id': product.id})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
