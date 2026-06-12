import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.users.models import User
from apps.contact.models import UserMessage


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username='sender',
        email='sender@example.com',
        password='pass123',
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpass123',
    )


@pytest.fixture
def message(db, user):
    return UserMessage.objects.create(
        user=user,
        subject='Wilted bouquet',
        body='The flowers arrived wilted, please advise.',
    )


@pytest.mark.django_db
class TestSendMessage:
    def test_send_requires_auth(self, api_client):
        url = reverse('contact-send')
        response = api_client.post(url, {'subject': 'Hi', 'body': 'Hello'}, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_user_can_send_message(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse('contact-send')
        response = api_client.post(
            url, {'subject': 'Question', 'body': 'Do you deliver on Sundays?'}, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        msg = UserMessage.objects.get(subject='Question')
        assert msg.user == user
        assert msg.is_read is False

    def test_subject_and_body_required(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse('contact-send')
        response = api_client.post(url, {'subject': ''}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestAdminMessages:
    def test_list_requires_admin(self, api_client, user, message):
        api_client.force_authenticate(user=user)
        url = reverse('contact-admin-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_list_messages(self, api_client, admin_user, message):
        api_client.force_authenticate(user=admin_user)
        url = reverse('contact-admin-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['user_email'] == message.user.email

    def test_retrieve_marks_message_read(self, api_client, admin_user, message):
        api_client.force_authenticate(user=admin_user)
        url = reverse('contact-admin-detail', kwargs={'pk': message.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        message.refresh_from_db()
        assert message.is_read is True

    def test_reply_sets_replied_at_and_read(self, api_client, admin_user, message):
        api_client.force_authenticate(user=admin_user)
        url = reverse('contact-admin-detail', kwargs={'pk': message.pk})
        response = api_client.patch(
            url, {'admin_reply': 'A replacement bouquet is on its way.'}, format='json')
        assert response.status_code == status.HTTP_200_OK
        message.refresh_from_db()
        assert message.admin_reply
        assert message.replied_at is not None
        assert message.is_read is True
