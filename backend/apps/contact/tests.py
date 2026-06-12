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

    def test_staff_cannot_write_to_support(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        url = reverse('contact-send')
        response = api_client.post(
            url, {'subject': 'Hi', 'body': 'I am support myself'}, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert UserMessage.objects.count() == 0


@pytest.mark.django_db
class TestMyMessages:
    def test_requires_auth(self, api_client):
        response = api_client.get(reverse('contact-my-list'))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_user_sees_only_own_messages(self, api_client, user, message):
        other = User.objects.create_user(
            username='other', email='other@example.com', password='pass123')
        UserMessage.objects.create(user=other, subject='Not yours', body='Private')

        api_client.force_authenticate(user=user)
        response = api_client.get(reverse('contact-my-list'))
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['subject'] == message.subject

    def test_includes_admin_reply(self, api_client, user, message):
        message.admin_reply = 'We are sending a fresh bouquet.'
        message.save(update_fields=['admin_reply'])

        api_client.force_authenticate(user=user)
        response = api_client.get(reverse('contact-my-list'))
        assert response.data['results'][0]['admin_reply'] == message.admin_reply


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

    def test_admin_can_send_multiple_chat_messages(self, api_client, admin_user, message):
        api_client.force_authenticate(user=admin_user)
        url = reverse('contact-admin-reply', kwargs={'pk': message.pk})

        first = api_client.post(url, {'body': 'First reply'}, format='json')
        second = api_client.post(url, {'body': 'Second reply'}, format='json')

        assert first.status_code == status.HTTP_201_CREATED
        assert second.status_code == status.HTTP_201_CREATED
        admin_messages = UserMessage.objects.filter(
            user=message.user,
            is_from_admin=True,
        ).order_by('created_at')
        assert list(admin_messages.values_list('body', flat=True)) == [
            'First reply',
            'Second reply',
        ]
        assert second.data['is_from_admin'] is True
