import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.users.models import User
from apps.categories.models import Category
from apps.products.models import Product


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def category(db):
    return Category.objects.create(name='Roses', slug='roses')


@pytest.fixture
def product(db, category):
    return Product.objects.create(
        name='Red Rose Bouquet',
        description='Beautiful red roses',
        price='29.99',
        category=category,
        stock=10,
        is_available=True,
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpass123',
    )


@pytest.mark.django_db
class TestProductList:
    def test_list_products(self, api_client, product):
        url = reverse('product-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 1

    def test_search_products(self, api_client, product):
        url = reverse('product-list')
        response = api_client.get(url, {'search': 'Rose'})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 1

    def test_filter_by_category(self, api_client, product, category):
        url = reverse('product-list')
        response = api_client.get(url, {'category': category.slug})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 1

    def test_filter_by_price(self, api_client, product):
        url = reverse('product-list')
        response = api_client.get(url, {'min_price': 10, 'max_price': 50})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 1


@pytest.mark.django_db
class TestProductDetail:
    def test_get_product_detail(self, api_client, product):
        url = reverse('product-detail', kwargs={'slug': product.slug})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == product.name

    def test_create_product_anonymous_unauthorized(self, api_client, category):
        url = reverse('product-list')
        data = {
            'name': 'New Product',
            'description': 'Test',
            'price': '15.00',
            'stock': 5,
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_product_requires_admin(self, api_client, category):
        regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='pass123',
        )
        api_client.force_authenticate(user=regular_user)
        url = reverse('product-list')
        data = {
            'name': 'New Product',
            'description': 'Test',
            'price': '15.00',
            'stock': 5,
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_create_product(self, api_client, admin_user, category):
        api_client.force_authenticate(user=admin_user)
        url = reverse('product-list')
        data = {
            'name': 'New Bouquet',
            'description': 'Fresh flowers',
            'price': '35.00',
            'stock': 8,
            'category_id': category.id,
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
