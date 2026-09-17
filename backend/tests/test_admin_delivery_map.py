"""The custom delivery map must respect admin visibility and safely show text."""

from decimal import Decimal
from unittest.mock import patch

import pytest
from apps.orders.models import Order
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.urls import reverse


@pytest.fixture
def staff(db):
    return get_user_model().objects.create_user(
        username='delivery-staff',
        email='delivery-staff@example.test',
        password='test',
        is_staff=True,
    )


@pytest.fixture
def customer(db):
    return get_user_model().objects.create_user(
        username='delivery-customer',
        email='delivery-customer@example.test',
        password='test',
    )


def permit(staff, codename):
    staff.user_permissions.add(
        Permission.objects.get(content_type__app_label='orders', codename=codename)
    )


def make_order(customer, address='Flower Street 12'):
    return Order.objects.create(
        user=customer,
        total_price=Decimal('125000.00'),
        shipping_address=address,
        phone='+998900000000',
        delivery_lat=Decimal('41.311081'),
        delivery_lng=Decimal('69.240562'),
    )


@pytest.mark.django_db
class TestAdminDeliveryMap:
    def test_staff_without_order_permission_cannot_view_customer_locations(
        self, staff, customer, client
    ):
        make_order(customer)
        client.force_login(staff)

        response = client.get(reverse('admin:orders_order_delivery_map'))

        assert response.status_code == 403
        assert customer.email not in response.content.decode()

    @pytest.mark.parametrize('codename', ['view_order', 'change_order'])
    def test_order_view_or_change_permission_allows_map(self, staff, customer, client, codename):
        permit(staff, codename)
        order = make_order(customer)
        client.force_login(staff)

        response = client.get(reverse('admin:orders_order_delivery_map'))

        assert response.status_code == 200
        assert [item['id'] for item in response.context['orders_data']] == [order.pk]

    def test_map_uses_admin_queryset_restrictions(self, staff, customer, client):
        permit(staff, 'view_order')
        visible = make_order(customer, 'Visible address')
        hidden = make_order(customer, 'Hidden address')
        client.force_login(staff)

        with patch.object(
            admin.site._registry[Order],
            'get_queryset',
            return_value=Order.objects.filter(pk=visible.pk),
        ):
            response = client.get(reverse('admin:orders_order_delivery_map'))

        assert response.status_code == 200
        assert [item['id'] for item in response.context['orders_data']] == [visible.pk]
        assert str(hidden.pk) not in [str(item['id']) for item in response.context['orders_data']]

    def test_customer_address_is_rendered_as_text_not_popup_html(self, staff, customer, client):
        permit(staff, 'view_order')
        payload = '<img src=x onerror=alert(1)>'
        make_order(customer, payload)
        client.force_login(staff)

        response = client.get(reverse('admin:orders_order_delivery_map'))
        body = response.content.decode()

        assert response.status_code == 200
        assert response.context['orders_data'][0]['address'] == payload
        assert payload not in body
        assert 'document.createTextNode(value)' in body
        assert 'marker.bindPopup(popup)' in body
