import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.users.models import User
from apps.reviews.models import Review

PRODUCT = 'pink-rose-harmony'


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username='petal', email='petal@example.com', password='pass123')


@pytest.fixture
def other_user(db):
    return User.objects.create_user(
        username='bloom', email='bloom@example.com', password='pass123')


@pytest.mark.django_db
class TestSummary:
    def test_guest_can_read_summary(self, api_client):
        url = reverse('product-social', kwargs={'product_id': PRODUCT})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['rating_average'] is None
        assert response.data['rating_count'] == 0
        assert response.data['my_review'] is None
        assert response.data['reviews'] == []

    def test_average_and_count_aggregate(self, api_client, user, other_user):
        Review.objects.create(product=PRODUCT, user=user, rating=5, body='Lovely')
        Review.objects.create(product=PRODUCT, user=other_user, rating=4, body='Nice')
        url = reverse('product-social', kwargs={'product_id': PRODUCT})
        response = api_client.get(url)
        assert response.data['rating_count'] == 2
        assert response.data['rating_average'] == 4.5

    def test_my_review_returned_when_authenticated(self, api_client, user):
        Review.objects.create(product=PRODUCT, user=user, rating=3, body='Ok')
        api_client.force_authenticate(user=user)
        url = reverse('product-social', kwargs={'product_id': PRODUCT})
        response = api_client.get(url)
        assert response.data['my_review'] == {'rating': 3, 'body': 'Ok'}
        assert response.data['reviews'][0]['is_mine'] is True


@pytest.mark.django_db
class TestReviewWrite:
    def test_review_requires_auth(self, api_client):
        url = reverse('product-review', kwargs={'product_id': PRODUCT})
        response = api_client.post(url, {'rating': 5, 'body': 'Hi'}, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_user_can_create_review(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse('product-review', kwargs={'product_id': PRODUCT})
        response = api_client.post(url, {'rating': 5, 'body': 'Gorgeous'}, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert Review.objects.count() == 1
        assert response.data['rating_average'] == 5.0
        assert response.data['my_review']['body'] == 'Gorgeous'

    def test_second_post_updates_not_duplicates(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse('product-review', kwargs={'product_id': PRODUCT})
        api_client.post(url, {'rating': 5, 'body': 'First'}, format='json')
        response = api_client.post(url, {'rating': 2, 'body': 'Changed my mind'}, format='json')
        assert Review.objects.filter(product=PRODUCT, user=user).count() == 1
        assert response.data['my_review'] == {'rating': 2, 'body': 'Changed my mind'}

    def test_rating_out_of_range_rejected(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse('product-review', kwargs={'product_id': PRODUCT})
        response = api_client.post(url, {'rating': 9}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Review.objects.count() == 0

    def test_user_can_delete_own_review(self, api_client, user):
        Review.objects.create(product=PRODUCT, user=user, rating=4, body='Bye soon')
        api_client.force_authenticate(user=user)
        url = reverse('product-review', kwargs={'product_id': PRODUCT})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_200_OK
        assert Review.objects.count() == 0
        assert response.data['my_review'] is None
