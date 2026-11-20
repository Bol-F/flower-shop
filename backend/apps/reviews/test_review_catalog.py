import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.products.models import Product
from apps.reviews.models import Review
from apps.users.models import User


@pytest.mark.django_db
@pytest.mark.parametrize('hidden', [False, True])
def test_reviews_require_a_visible_catalog_product(hidden):
    user = User.objects.create_user(username='review-shopper', email='review-shopper@example.test')
    if hidden:
        Product.objects.create(
            name='Hidden roses',
            slug='unlisted',
            description='Flowers',
            price=25,
            is_available=False,
        )
    client = APIClient()
    client.force_authenticate(user)

    response = client.post(
        reverse('product-review', args=['unlisted']), {'rating': 5}, format='json'
    )

    assert response.status_code == 404
    assert not Review.objects.exists()
    assert client.get(reverse('product-social', args=['unlisted'])).status_code == 404


@pytest.mark.django_db
def test_rating_aggregates_match_catalog_after_update_and_delete():
    user = User.objects.create_user(username='rating-shopper', email='rating-shopper@example.test')
    product = Product.objects.create(name='Rating roses', description='Flowers', price=25)
    client = APIClient()
    client.force_authenticate(user)
    review_url = reverse('product-review', args=[product.slug])
    catalog_url = reverse('product-detail', args=[product.slug])

    for rating in [5, 2]:
        response = client.post(review_url, {'rating': rating}, format='json')
        catalog = client.get(catalog_url)
        assert response.data['rating_count'] == catalog.data['rating_count'] == 1
        assert response.data['rating_average'] == catalog.data['rating_average'] == rating
    client.delete(review_url)
    catalog = client.get(catalog_url)
    assert catalog.data['rating_count'] == 0
    assert catalog.data['rating_average'] is None
