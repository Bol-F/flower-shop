"""Order administration must preserve verified payment and dispatch updates."""

from decimal import Decimal

import pytest
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone

from .models import Order


@pytest.fixture
def order_admin_context(db):
    manager = get_user_model().objects.create_superuser(
        username='order-edit-manager', email='order-edit-manager@example.test', password='test'
    )
    order = Order.objects.create(
        user=manager,
        total_price=Decimal('25.00'),
        shipping_address='Flower Street',
        phone='+998901234567',
        payment_method=Order.PaymentMethod.CARD,
        payment_status=Order.PaymentStatus.PENDING,
    )
    request = RequestFactory().post(f'/admin/orders/order/{order.pk}/change/')
    request.user = manager
    return admin.site._registry[Order], request, order


def edit_form(model_admin, request, order, **changes):
    form_type = model_admin.get_form(request, obj=order)
    return form_type(
        data={'shipping_address': order.shipping_address, 'phone': order.phone, **changes},
        instance=order,
    )


def test_note_edit_preserves_verified_payment_and_fulfillment(order_admin_context):
    model_admin, request, order = order_admin_context
    form = edit_form(model_admin, request, order, notes='Use the side entrance')
    assert form.is_valid(), form.errors
    edited = form.save(commit=False)
    paid_at = timezone.now()
    Order.objects.filter(pk=order.pk).update(
        status=Order.Status.DELIVERED,
        payment_status=Order.PaymentStatus.PAID,
        payment_provider='payme',
        payment_reference='verified-reference',
        paid_at=paid_at,
        delivered_at=paid_at,
        loyalty_points_earned=25,
    )

    model_admin.save_model(request, edited, form, change=True)

    order.refresh_from_db()
    assert order.notes == 'Use the side entrance'
    assert order.status == Order.Status.DELIVERED
    assert order.payment_status == Order.PaymentStatus.PAID
    assert order.payment_provider == 'payme'
    assert order.payment_reference == 'verified-reference'
    assert order.paid_at == paid_at
    assert order.delivered_at == paid_at
    assert order.loyalty_points_earned == 25


def test_note_edit_preserves_address_changed_by_another_editor(order_admin_context):
    model_admin, request, order = order_admin_context
    form = edit_form(model_admin, request, order, notes='Handle gently')
    assert form.is_valid(), form.errors
    Order.objects.filter(pk=order.pk).update(shipping_address='New dispatch address')

    model_admin.save_model(request, form.save(commit=False), form, change=True)

    order.refresh_from_db()
    assert order.notes == 'Handle gently'
    assert order.shipping_address == 'New dispatch address'


def test_terminal_transition_prevents_stale_address_changes(order_admin_context):
    model_admin, request, order = order_admin_context
    form = edit_form(model_admin, request, order, shipping_address='Too late', notes='Archive note')
    assert form.is_valid(), form.errors
    Order.objects.filter(pk=order.pk).update(status=Order.Status.DELIVERED)

    model_admin.save_model(request, form.save(commit=False), form, change=True)

    order.refresh_from_db()
    assert order.status == Order.Status.DELIVERED
    assert order.shipping_address == 'Flower Street'
    assert order.notes == 'Archive note'


def test_real_admin_change_form_saves_delivery_notes(order_admin_context, client):
    _, request, order = order_admin_context
    client.force_login(request.user)
    url = reverse('admin:orders_order_change', args=[order.pk])
    response = client.get(url)
    assert response.status_code == 200
    data = {
        'shipping_address': 'Updated dispatch address',
        'phone': order.phone,
        'notes': 'Saved through administration',
        '_save': 'Save',
    }
    for inline in response.context['inline_admin_formsets']:
        for field in inline.formset.management_form:
            data[field.html_name] = field.value()

    response = client.post(url, data)

    assert response.status_code == 302
    order.refresh_from_db()
    assert order.shipping_address == 'Updated dispatch address'
    assert order.notes == 'Saved through administration'
    assert order.payment_status == Order.PaymentStatus.PENDING
