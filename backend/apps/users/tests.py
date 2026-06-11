import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.users.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_data():
    return {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'StrongPass123!',
        'password_confirm': 'StrongPass123!',
    }


@pytest.fixture
def created_user(db, user_data):
    user = User.objects.create_user(
        username=user_data['username'],
        email=user_data['email'],
        password=user_data['password'],
    )
    return user


@pytest.mark.django_db
class TestRegistration:
    def test_register_success(self, api_client, user_data):
        url = reverse('register')
        response = api_client.post(url, user_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['email'] == user_data['email']
        assert User.objects.filter(email=user_data['email']).exists()

    def test_register_password_mismatch(self, api_client, user_data):
        user_data['password_confirm'] = 'WrongPassword'
        url = reverse('register')
        response = api_client.post(url, user_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_duplicate_email(self, api_client, user_data, created_user):
        url = reverse('register')
        response = api_client.post(url, user_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestLogin:
    def test_login_success(self, api_client, created_user, user_data):
        url = reverse('login')
        response = api_client.post(
            url,
            {'email': user_data['email'], 'password': user_data['password']},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data

    def test_login_wrong_password(self, api_client, created_user, user_data):
        url = reverse('login')
        response = api_client.post(
            url,
            {'email': user_data['email'], 'password': 'wrongpassword'},
            format='json',
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_profile_requires_auth(self, api_client):
        url = reverse('profile')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_profile_authenticated(self, api_client, created_user):
        api_client.force_authenticate(user=created_user)
        url = reverse('profile')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == created_user.email
