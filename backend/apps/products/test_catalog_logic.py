import pytest
from django.contrib.auth.models import Permission
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework.test import APIClient

from apps.categories.models import Category
from apps.marketplace.models import City, Vendor, WishlistItem
from apps.products.models import Product
from apps.reviews.models import Review
from apps.users.models import User


@pytest.fixture
def shopper(db):
    return User.objects.create_user(username='catalog-shopper', email='catalog@example.test')


def bouquet(name='Garden roses', **kwargs):
    return Product.objects.create(name=name, description='Fresh flowers', price='25.00', **kwargs)


@pytest.mark.django_db
@pytest.mark.parametrize('inactive', ['product', 'city', 'vendor', 'vendor_city'])
def test_hidden_catalog_entries_are_not_public_or_addable_to_wishlist(shopper, inactive):
    city = City.objects.create(name='Catalog city', is_active=inactive != 'city')
    vendor_city = City.objects.create(name='Florist city', is_active=inactive != 'vendor_city')
    vendor = Vendor.objects.create(
        name='Garden florist', city=vendor_city, is_active=inactive != 'vendor'
    )
    product = bouquet(city=city, vendor=vendor, is_available=inactive != 'product')
    client = APIClient()
    assert client.get(reverse('product-list')).data['count'] == 0
    assert client.get(reverse('product-detail', args=[product.slug])).status_code == 404
    client.force_authenticate(shopper)
    response = client.post(reverse('wishlist'), {'product_id': product.pk}, format='json')
    assert response.status_code == 400
    assert not WishlistItem.objects.exists()


@pytest.mark.django_db
def test_catalog_staff_can_inspect_hidden_products(shopper):
    shopper.is_staff = True
    shopper.save(update_fields=['is_staff'])
    shopper.user_permissions.add(
        Permission.objects.get(content_type__app_label='products', codename='view_product')
    )
    product = bouquet(is_available=False)
    client = APIClient()
    client.force_authenticate(shopper)
    assert client.get(reverse('product-detail', args=[product.slug])).status_code == 200


@pytest.mark.django_db
def test_wishlist_ratings_match_catalog_and_queries_do_not_grow_per_product(shopper):
    client = APIClient()
    client.force_authenticate(shopper)
    city = City.objects.create(name='Wishlist city')
    vendor = Vendor.objects.create(name='Wishlist florist', city=city)
    for index in range(4):
        product = bouquet(name=f'Wishlist roses {index}', city=city, vendor=vendor)
        WishlistItem.objects.create(user=shopper, product=product)
        Review.objects.create(user=shopper, product=product.slug, rating=4)

    with CaptureQueriesContext(connection) as queries:
        response = client.get(reverse('wishlist'))

    assert response.status_code == 200
    assert len(queries) <= 3
    for item in response.data['results']:
        assert item['product']['rating_average'] == 4
        assert item['product']['rating_count'] == 1
        assert item['product']['city_name'] == city.name


@pytest.mark.django_db
def test_category_counts_only_include_public_products_without_per_category_queries():
    for index in reversed(range(4)):
        category = Category.objects.create(name=f'Category {index}')
        bouquet(name=f'Visible roses {index}', category=category)
        bouquet(name=f'Hidden roses {index}', category=category, is_available=False)
    with CaptureQueriesContext(connection) as queries:
        response = APIClient().get(reverse('category-list'))
    assert response.status_code == 200
    assert len(queries) <= 2
    assert [row['name'] for row in response.data['results']] == [
        f'Category {index}' for index in range(4)
    ]
    assert [row['product_count'] for row in response.data['results']] == [1, 1, 1, 1]


@pytest.mark.django_db
@pytest.mark.parametrize(
    'model,url_name,payload',
    [
        (Category, 'category-list', {'name': 'Garden roses!'}),
        (
            Product,
            'product-list',
            {'name': 'Garden roses!', 'description': 'Fresh flowers', 'price': '25.00'},
        ),
    ],
)
def test_catalog_api_rejects_names_whose_generated_slug_already_exists(model, url_name, payload):
    if model is Category:
        Category.objects.create(name='Garden roses')
    else:
        bouquet()
    staff = User.objects.create_superuser(username='slug-api-admin', email='slug-api@example.test')
    client = APIClient()
    client.force_authenticate(staff)
    response = client.post(reverse(url_name), payload, format='json')
    assert response.status_code == 400
    assert 'name' in response.data
