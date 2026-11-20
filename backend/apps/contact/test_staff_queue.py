import pytest
from django.contrib.auth.models import Permission
from django.urls import reverse
from rest_framework.test import APIClient

from apps.contact.models import UserMessage
from apps.users.models import User


@pytest.mark.django_db
def test_support_queue_global_search_exact_customer_and_pagination():
    staff = User.objects.create_user(
        username='inbox-staff', email='inbox@example.test', is_staff=True
    )
    staff.user_permissions.add(
        Permission.objects.get(content_type__app_label='contact', codename='view_usermessage')
    )
    first = User.objects.create_user(username='Daria', email='daria@example.test')
    second = User.objects.create_user(username='Alex', email='alex@example.test')
    for index in range(3):
        UserMessage.objects.create(user=first, subject='Bouquet question', body=f'Flowers {index}')
    UserMessage.objects.create(user=second, subject='Other customer', body='Private')
    client = APIClient()
    client.force_authenticate(staff)
    url = reverse('contact-admin-list')
    searched = client.get(url, {'search': 'Daria', 'page_size': 1})
    assert searched.status_code == 200
    assert searched.data['count'] == 3
    assert searched.data['next']
    selected = client.get(url, {'user__email': first.email, 'page_size': 2, 'page': 2})
    assert selected.data['count'] == 3
    assert len(selected.data['results']) == 1
    assert selected.data['results'][0]['user_email'] == first.email
    assert not selected.data['next']


@pytest.mark.django_db
def test_support_filters_do_not_bypass_permissions():
    staff = User.objects.create_user(
        username='restricted-inbox', email='restricted@example.test', is_staff=True
    )
    client = APIClient()
    client.force_authenticate(staff)
    assert client.get(reverse('contact-admin-list'), {'search': 'Daria'}).status_code == 403


@pytest.mark.django_db
def test_clearing_support_reply_clears_its_timestamp():
    staff = User.objects.create_superuser(username='reply-staff', email='reply@example.test')
    customer = User.objects.create_user(
        username='reply-customer', email='reply-customer@example.test'
    )
    message = UserMessage.objects.create(user=customer, subject='Question', body='Delivery?')
    client = APIClient()
    client.force_authenticate(staff)
    url = reverse('contact-admin-detail', args=[message.pk])
    assert client.patch(url, {'admin_reply': 'Tomorrow'}, format='json').status_code == 200
    assert client.patch(url, {'admin_reply': ''}, format='json').status_code == 200
    message.refresh_from_db()
    assert message.replied_at is None


@pytest.mark.django_db
def test_outgoing_support_message_cannot_be_rewritten_as_an_incoming_reply():
    staff = User.objects.create_superuser(username='outgoing-staff', email='outgoing@example.test')
    customer = User.objects.create_user(
        username='outgoing-customer', email='outgoing-customer@example.test'
    )
    message = UserMessage.objects.create(
        user=customer, subject='Reply', body='Answer', is_from_admin=True, is_read=True
    )
    client = APIClient()
    client.force_authenticate(staff)
    response = client.patch(
        reverse('contact-admin-detail', args=[message.pk]),
        {'admin_reply': 'Nested reply'},
        format='json',
    )
    assert response.status_code == 400
    message.refresh_from_db()
    assert not message.admin_reply
