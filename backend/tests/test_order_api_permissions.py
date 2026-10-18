"""Staff API permissions follow the Django Order model, not the staff flag.

Customers (including staff purchasing personally) keep owner-scoped access.
Cross-customer order/payment reads require view_order, changes to payment and
fulfillment require change_order, and the mixed inventory dashboard additionally
requires view_product. Group permissions and superusers follow Django's backend.
"""

import pytest
from django.contrib.auth.models import Group, Permission
from django.urls import reverse
from rest_framework.test import APIClient

from apps.orders.models import Order, OrderItem, PaymentAttempt, PaymentEvent
from apps.users.models import User


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def customer(db):
    return User.objects.create_user('customer', 'customer@example.test', 'password')


@pytest.fixture
def staff(db):
    return User.objects.create_user('staff', 'staff@example.test', 'password', is_staff=True)


def grant(user, *permissions):
    for name in permissions:
        app_label, codename = name.split('.')
        user.user_permissions.add(
            Permission.objects.get(content_type__app_label=app_label, codename=codename)
        )
    return User.objects.get(pk=user.pk)


def make_order(user, **overrides):
    values = {
        'user': user,
        'total_price': '25.00',
        'shipping_address': 'Private customer address',
        'phone': '+998901234567',
        'payment_method': Order.PaymentMethod.CASH,
    }
    values.update(overrides)
    return Order.objects.create(**values)


@pytest.fixture
def order(customer):
    return make_order(customer)


@pytest.fixture
def payment(order):
    return PaymentAttempt.objects.create(
        order=order, provider='cash', amount='25.00', idempotency_key='test-cash'
    )


WRITE_OPERATIONS = (
    ('order-status-update', 'patch', {'status': Order.Status.CONFIRMED}),
    ('order-courier-assign', 'patch', {'courier_id': None}),
    (
        'order-payment-status-update',
        'patch',
        {'payment_status': Order.PaymentStatus.PAID, 'reason': 'Cash received'},
    ),
    ('order-cancel', 'post', {}),
)


@pytest.mark.django_db
class TestStaffOrderPermissions:
    def test_staff_without_permissions_sees_only_personal_orders(
        self, client, staff, order, payment
    ):
        own_order = make_order(staff)
        client.force_authenticate(staff)

        response = client.get(reverse('order-list'))
        assert response.status_code == 200
        assert response.data['count'] == 1
        assert [item['id'] for item in response.data['results']] == [own_order.pk]
        assert client.get(reverse('order-detail', args=[order.pk])).status_code == 403
        assert (
            client.get(reverse('payment-detail', args=[order.pk, payment.public_id])).status_code
            == 404
        )
        assert client.post(reverse('order-repeat', args=[order.pk])).status_code == 403
        assert client.get(reverse('order-dashboard')).status_code == 403

    @pytest.mark.parametrize('permission', [None, 'orders.view_order', 'products.change_product'])
    @pytest.mark.parametrize('url_name,method,payload', WRITE_OPERATIONS)
    def test_staff_requires_order_change_permission_before_mutating(
        self, client, staff, order, permission, url_name, method, payload
    ):
        if permission:
            staff = grant(staff, permission)
        client.force_authenticate(staff)

        response = getattr(client, method)(
            reverse(url_name, args=[order.pk]), payload, format='json'
        )

        assert response.status_code == 403
        order.refresh_from_db()
        assert order.status == Order.Status.PENDING
        assert order.payment_status == Order.PaymentStatus.UNPAID
        assert order.assigned_courier_id is None
        assert order.inventory_released_at is None
        assert not PaymentEvent.objects.exists()

    @pytest.mark.parametrize('url_name,method,payload', WRITE_OPERATIONS)
    def test_explicit_order_change_permission_allows_staff_operations(
        self, client, staff, order, url_name, method, payload
    ):
        client.force_authenticate(grant(staff, 'orders.change_order'))
        response = getattr(client, method)(
            reverse(url_name, args=[order.pk]), payload, format='json'
        )
        assert response.status_code == 200

    def test_view_permission_allows_cross_customer_reads_and_repeat(
        self, client, staff, order, payment
    ):
        client.force_authenticate(grant(staff, 'orders.view_order'))
        assert client.get(reverse('order-list')).data['count'] == 1
        detail = client.get(reverse('order-detail', args=[order.pk]))
        assert detail.status_code == 200
        assert detail.data['id'] == order.pk
        payment_response = client.get(reverse('payment-detail', args=[order.pk, payment.public_id]))
        assert payment_response.status_code == 200
        assert payment_response.data['order_id'] == order.pk
        assert client.post(reverse('order-repeat', args=[order.pk])).status_code == 200

    def test_group_permissions_are_respected(self, client, staff, order):
        group = Group.objects.create(name='Order readers')
        group.permissions.add(
            Permission.objects.get(content_type__app_label='orders', codename='view_order')
        )
        staff.groups.add(group)
        client.force_authenticate(staff)
        assert client.get(reverse('order-detail', args=[order.pk])).status_code == 200

    @pytest.mark.parametrize(
        'permissions,expected',
        [
            ((), 403),
            (('orders.view_order',), 403),
            (('products.view_product',), 403),
            (('orders.view_order', 'products.view_product'), 200),
        ],
    )
    def test_mixed_dashboard_requires_both_data_permissions(
        self, client, staff, order, permissions, expected
    ):
        client.force_authenticate(grant(staff, *permissions))
        assert client.get(reverse('order-dashboard')).status_code == expected

    @pytest.mark.parametrize('url_name,method,payload', WRITE_OPERATIONS)
    def test_non_staff_model_permissions_cannot_grant_staff_operations(
        self, client, customer, order, url_name, method, payload
    ):
        client.force_authenticate(grant(customer, 'orders.change_order'))
        response = getattr(client, method)(
            reverse(url_name, args=[order.pk]), payload, format='json'
        )
        # Cancelling an unpaid personal order is a customer operation, not a staff privilege.
        assert response.status_code == (200 if url_name == 'order-cancel' else 403)

    def test_non_staff_read_permission_does_not_expand_customer_scope(
        self, client, customer, staff
    ):
        other_order = make_order(staff)
        client.force_authenticate(grant(customer, 'orders.view_order', 'products.view_product'))
        assert client.get(reverse('order-list')).data['count'] == 0
        assert client.get(reverse('order-detail', args=[other_order.pk])).status_code == 403
        assert client.get(reverse('order-dashboard')).status_code == 403

    def test_staff_retains_personal_customer_workflows_without_model_permissions(
        self, client, staff
    ):
        own_order = make_order(staff)
        payment = PaymentAttempt.objects.create(
            order=own_order, provider='cash', amount='25.00', idempotency_key='personal'
        )
        client.force_authenticate(staff)
        assert client.get(reverse('order-detail', args=[own_order.pk])).status_code == 200
        assert (
            client.get(
                reverse('payment-detail', args=[own_order.pk, payment.public_id])
            ).status_code
            == 200
        )
        assert client.post(reverse('order-repeat', args=[own_order.pk])).status_code == 200
        assert client.post(reverse('order-cancel', args=[own_order.pk])).status_code == 200

    @pytest.mark.parametrize('url_name,method,payload', WRITE_OPERATIONS)
    def test_superuser_remains_authorized(self, client, order, url_name, method, payload):
        admin = User.objects.create_superuser('owner', 'owner@example.test', 'password')
        client.force_authenticate(admin)
        assert (
            getattr(client, method)(
                reverse(url_name, args=[order.pk]), payload, format='json'
            ).status_code
            == 200
        )

    def test_superuser_can_read_all_orders_payments_and_dashboard(self, client, order, payment):
        admin = User.objects.create_superuser('owner', 'owner@example.test', 'password')
        client.force_authenticate(admin)
        assert client.get(reverse('order-list')).data['count'] == 1
        assert client.get(reverse('order-detail', args=[order.pk])).status_code == 200
        assert (
            client.get(reverse('payment-detail', args=[order.pk, payment.public_id])).status_code
            == 200
        )
        assert client.get(reverse('order-dashboard')).status_code == 200


@pytest.mark.django_db
def test_best_selling_counts_only_paid_non_cancelled_items(client, customer, staff):
    client.force_authenticate(grant(staff, 'orders.view_order', 'products.view_product'))
    for price, quantity, order_status, payment_status in (
        ('10.00', 2, Order.Status.CONFIRMED, Order.PaymentStatus.PAID),
        ('20.00', 1, Order.Status.DELIVERED, Order.PaymentStatus.PAID),
        ('10.00', 100, Order.Status.CANCELLED, Order.PaymentStatus.PAID),
        ('10.00', 100, Order.Status.PENDING, Order.PaymentStatus.UNPAID),
        ('10.00', 100, Order.Status.PENDING, Order.PaymentStatus.PENDING),
        ('10.00', 100, Order.Status.PENDING, Order.PaymentStatus.FAILED),
        ('10.00', 100, Order.Status.DELIVERED, Order.PaymentStatus.REFUNDED),
    ):
        order = make_order(customer, status=order_status, payment_status=payment_status)
        OrderItem.objects.create(
            order=order, product_name='Roses', product_price=price, quantity=quantity
        )
    unpaid_only = make_order(customer)
    OrderItem.objects.create(
        order=unpaid_only, product_name='Not actually sold', product_price='99.00', quantity=500
    )

    response = client.get(reverse('order-dashboard'))
    assert response.status_code == 200
    assert response.data['best_selling_products'] == [
        {'product_name': 'Roses', 'quantity_sold': 3, 'revenue': '40.00'}
    ]
