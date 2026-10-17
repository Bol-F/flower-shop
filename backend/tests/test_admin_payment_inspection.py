from datetime import timedelta

import pytest
from django.contrib.auth.models import Permission
from django.urls import reverse
from django.utils import timezone

from apps.orders.models import Order, PaymentAttempt, PaymentEvent
from apps.users.models import SocialIdentity, User


@pytest.fixture
def owner(db):
    return User.objects.create_superuser('owner', 'owner@example.test', 'password')


@pytest.mark.django_db
def test_order_payment_history_and_event_history_are_read_only(client, owner):
    order = Order.objects.create(user=owner, total_price='10', phone='998', shipping_address='Test')
    payment = PaymentAttempt.objects.create(
        order=order,
        provider='payme',
        amount='126500',
        idempotency_key='test',
    )
    PaymentEvent.objects.create(
        payment=payment,
        source='provider',
        event_type='payme_create_transaction',
        status_to='processing',
    )
    client.force_login(owner)
    response = client.get(reverse('admin:orders_order_change', args=[order.pk]))
    assert response.status_code == 200
    inline = next(
        i for i in response.context['inline_admin_formsets'] if i.opts.model == PaymentAttempt
    )
    assert not inline.has_add_permission
    assert not inline.has_change_permission
    assert not inline.has_delete_permission
    assert str(payment.public_id) in response.content.decode()
    response = client.get(reverse('admin:orders_paymentattempt_change', args=[payment.pk]))
    inline = response.context['inline_admin_formsets'][0]
    assert 'payme_create_transaction' in response.content.decode()
    assert not inline.has_change_permission
    assert not inline.has_delete_permission


@pytest.mark.django_db
def test_attention_filters_preserve_completed_and_cancelled_order_boundaries(client, owner):
    yesterday = timezone.localdate() - timedelta(days=1)
    kwargs = {
        'user': owner,
        'total_price': '10',
        'phone': '998',
        'shipping_address': 'Test',
        'delivery_date': yesterday,
    }
    active = Order.objects.create(**kwargs, payment_method='card', payment_status='pending')
    delivered_cash = Order.objects.create(
        **kwargs, status='delivered', payment_method='cash', payment_status='unpaid'
    )
    Order.objects.create(
        **kwargs, status='cancelled', payment_method='cash', payment_status='unpaid'
    )
    client.force_login(owner)
    for attention, expected in [
        ('payment', active.pk),
        ('overdue', active.pk),
        ('cash', delivered_cash.pk),
    ]:
        response = client.get(reverse('admin:orders_order_changelist'), {'attention': attention})
        assert list(response.context['cl'].queryset.values_list('pk', flat=True)) == [expected]


@pytest.mark.django_db
def test_customer_manager_cannot_see_identity_details_without_permission(client, owner):
    manager = User.objects.create_user('manager', 'manager@example.test', 'password', is_staff=True)
    customer = User.objects.create_user('customer', 'customer@example.test', 'password')
    manager.user_permissions.add(Permission.objects.get(codename='view_user'))
    SocialIdentity.objects.create(
        user=customer,
        provider='google',
        issuer='https://accounts.google.com',
        subject='private-subject',
    )
    client.force_login(manager)
    response = client.get(reverse('admin:users_user_change', args=[customer.pk]))
    assert response.status_code == 200
    assert not any(
        i.opts.model == SocialIdentity for i in response.context['inline_admin_formsets']
    )
