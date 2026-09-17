"""Staff fulfillment operations should preserve payment and order history."""

from datetime import timedelta
from decimal import Decimal

import pytest
from apps.marketplace.models import City, Courier
from apps.orders.fulfillment import assign_order_courier, change_order_status
from apps.orders.models import DeliveryZone, NotificationLog, Order
from apps.orders.pricing import calculate_delivery_fee
from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.urls import reverse
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient


@pytest.fixture
def customer(db):
    return get_user_model().objects.create_user(
        username='order-customer', email='order-customer@example.test', password='test'
    )


@pytest.fixture
def manager(db):
    return get_user_model().objects.create_superuser(
        username='order-manager', email='order-manager@example.test', password='test'
    )


def make_order(customer, **kwargs):
    return Order.objects.create(
        user=customer,
        total_price=Decimal('25.00'),
        shipping_address='Flower Street',
        phone='+998901234567',
        **kwargs,
    )


@pytest.mark.django_db
class TestOrderFulfillment:
    def test_noop_does_not_send_duplicate_notifications(self, customer):
        order = make_order(customer)
        order, changed = change_order_status(order, Order.Status.CONFIRMED)
        assert changed is True
        before = NotificationLog.objects.filter(related_order=order).count()
        _, changed = change_order_status(order, Order.Status.CONFIRMED)
        assert changed is False
        assert NotificationLog.objects.filter(related_order=order).count() == before

    def test_cancelled_and_backwards_transitions_are_rejected(self, customer):
        cancelled = make_order(customer, status=Order.Status.CANCELLED)
        with pytest.raises(ValidationError):
            change_order_status(cancelled, Order.Status.DELIVERED)
        preparing = make_order(customer, status=Order.Status.PREPARING)
        with pytest.raises(ValidationError):
            change_order_status(preparing, Order.Status.CONFIRMED)

    def test_unpaid_card_cannot_be_fulfilled(self, customer):
        card = make_order(
            customer,
            payment_method=Order.PaymentMethod.CARD,
            payment_status=Order.PaymentStatus.PENDING,
        )
        with pytest.raises(ValidationError):
            change_order_status(card, Order.Status.DELIVERED)
        card.refresh_from_db()
        assert card.status == Order.Status.PENDING
        assert NotificationLog.objects.filter(related_order=card).count() == 0

    def test_active_matching_courier_only_and_timestamp(self, customer):
        city = City.objects.create(name='Tashkent Dispatch')
        other_city = City.objects.create(name='Samarkand Dispatch')
        order = make_order(customer, city=city)
        user = get_user_model().objects.create_user(
            username='courier', email='courier@example.test', password='test'
        )
        courier = Courier.objects.create(
            user=user, city=other_city, current_status=Courier.Status.AVAILABLE
        )
        with pytest.raises(ValidationError):
            assign_order_courier(order, courier)
        courier.city = city
        courier.save(update_fields=['city'])
        order, changed = assign_order_courier(order, courier)
        assert changed is True
        assert order.courier_assigned_at is not None
        _, changed = assign_order_courier(order, courier)
        assert changed is False
        courier.current_status = Courier.Status.OFFLINE
        courier.save(update_fields=['current_status'])
        with pytest.raises(ValidationError):
            assign_order_courier(make_order(customer, city=city), courier)

    def test_admin_bulk_action_skips_ineligible_and_logs_changes(self, customer, manager, client):
        eligible = make_order(customer)
        cancelled = make_order(customer, status=Order.Status.CANCELLED)
        client.force_login(manager)
        response = client.post(
            reverse('admin:orders_order_changelist'),
            {
                'action': 'mark_delivered',
                '_selected_action': [eligible.pk, cancelled.pk],
                'index': '0',
            },
        )
        assert response.status_code == 302
        eligible.refresh_from_db()
        cancelled.refresh_from_db()
        assert eligible.status == Order.Status.DELIVERED
        assert eligible.delivered_at is not None
        assert cancelled.status == Order.Status.CANCELLED
        assert LogEntry.objects.filter(object_id=str(eligible.pk)).exists()
        assert not LogEntry.objects.filter(object_id=str(cancelled.pk)).exists()

    def test_admin_courier_action_has_confirmation_and_rejects_terminal_order(
        self, customer, manager, client
    ):
        open_order = make_order(customer)
        terminal = make_order(customer, status=Order.Status.DELIVERED)
        user = get_user_model().objects.create_user(
            username='dispatch-courier', email='dispatch-courier@example.test', password='test'
        )
        courier = Courier.objects.create(user=user, current_status=Courier.Status.AVAILABLE)
        client.force_login(manager)
        url = reverse('admin:orders_order_changelist')
        selected = {
            'action': 'assign_courier',
            '_selected_action': [open_order.pk, terminal.pk],
            'index': '0',
        }
        confirmation = client.post(url, selected)
        assert confirmation.status_code == 200
        assert 'Assign courier' in confirmation.content.decode()
        response = client.post(url, {**selected, 'courier': courier.pk, 'apply': '1'})
        assert response.status_code == 302
        open_order.refresh_from_db()
        terminal.refresh_from_db()
        assert open_order.assigned_courier_id == courier.pk
        assert open_order.courier_assigned_at is not None
        assert terminal.assigned_courier_id is None

    def test_admin_change_form_cannot_rewrite_financial_or_fulfillment_fields(
        self, customer, manager, client
    ):
        order = make_order(customer)
        model_admin = admin.site._registry[Order]
        assert model_admin.has_add_permission(None) is False
        assert {'status', 'payment_method', 'assigned_courier', 'promo_code'} <= set(
            model_admin.readonly_fields
        )
        client.force_login(manager)
        response = client.post(
            reverse('admin:orders_order_change', args=[order.pk]),
            {
                'status': Order.Status.DELIVERED,
                'payment_method': Order.PaymentMethod.CARD,
                'total_price': '0',
                'assigned_courier': '999',
                'shipping_address': 'Updated Flower Street',
                'phone': '+998901234567',
            },
        )
        assert response.status_code in (200, 302)
        order.refresh_from_db()
        assert order.status == Order.Status.PENDING
        assert order.payment_method == Order.PaymentMethod.CASH
        assert order.total_price == Decimal('25.00')
        assert order.assigned_courier_id is None

    def test_view_only_staff_has_no_mutating_order_actions(self, customer):
        staff = get_user_model().objects.create_user(
            username='viewer', email='viewer@example.test', password='test', is_staff=True
        )
        staff.user_permissions.add(
            Permission.objects.get(content_type__app_label='orders', codename='view_order')
        )
        from django.test import RequestFactory

        request = RequestFactory().get('/admin/orders/order/')
        request.user = staff
        actions = admin.site._registry[Order].get_actions(request)
        assert not {'mark_cash_paid', 'assign_courier', 'mark_delivered'} & set(actions)

    def test_staff_api_rejects_invalid_and_idempotently_accepts_noop(self, customer, manager):
        card = make_order(
            customer,
            payment_method=Order.PaymentMethod.CARD,
            payment_status=Order.PaymentStatus.PENDING,
        )
        api = APIClient()
        api.force_authenticate(user=manager)
        url = reverse('order-status-update', args=[card.pk])
        invalid = api.patch(url, {'status': Order.Status.DELIVERED}, format='json')
        assert invalid.status_code == 400
        assert NotificationLog.objects.filter(related_order=card).count() == 0
        confirmed = api.patch(url, {'status': Order.Status.CONFIRMED}, format='json')
        assert confirmed.status_code == 200
        before = NotificationLog.objects.filter(related_order=card).count()
        noop = api.patch(url, {'status': Order.Status.CONFIRMED}, format='json')
        assert noop.status_code == 200
        assert NotificationLog.objects.filter(related_order=card).count() == before

    def test_negative_delivery_fee_is_rejected_in_admin_and_checkout(self, manager):
        from django.test import RequestFactory

        request = RequestFactory().get('/admin/orders/deliveryzone/add/')
        request.user = manager
        zone = DeliveryZone(name='Broken zone', fee=Decimal('-1.00'))
        form_type = admin.site._registry[DeliveryZone].get_form(request)
        form = form_type(data={'name': 'Broken zone', 'fee': '-1.00', 'is_active': 'on'})
        assert not form.is_valid()
        assert 'fee' in form.errors
        with pytest.raises(ValidationError):
            calculate_delivery_fee(Decimal('10.00'), zone)

    def test_admin_rejects_past_delivery_dates_and_partial_map_points(self, customer, manager):
        from django.test import RequestFactory

        order = make_order(customer)
        request = RequestFactory().post('/admin/orders/order/')
        request.user = manager
        form_type = admin.site._registry[Order].get_form(request, obj=order)
        form = form_type(
            data={
                'shipping_address': 'Flower Street',
                'phone': '+998901234567',
                'delivery_date': (timezone.localdate() - timedelta(days=1)).isoformat(),
                'delivery_lat': '41.311081',
                'delivery_lng': '',
            },
            instance=order,
        )
        assert not form.is_valid()
        assert {'delivery_date', 'delivery_lat'} <= set(form.errors)

    def test_terminal_order_recipient_and_address_are_immutable(self, customer, manager, client):
        order = make_order(
            customer,
            status=Order.Status.DELIVERED,
            recipient_name='Original recipient',
            delivery_address='Original delivery address',
        )
        model_admin = admin.site._registry[Order]
        from django.test import RequestFactory

        request = RequestFactory().get('/admin/orders/order/')
        request.user = manager
        assert {'recipient_name', 'delivery_address', 'shipping_address'} <= set(
            model_admin.get_readonly_fields(request, order)
        )
        client.force_login(manager)
        response = client.post(
            reverse('admin:orders_order_change', args=[order.pk]),
            {
                'recipient_name': 'Forged recipient',
                'delivery_address': 'Forged address',
                'shipping_address': 'Forged shipping address',
                'phone': '+998901111111',
                'notes': 'Operational note',
            },
        )
        assert response.status_code in (200, 302)
        order.refresh_from_db()
        assert order.recipient_name == 'Original recipient'
        assert order.delivery_address == 'Original delivery address'
        assert order.shipping_address == 'Flower Street'
