import pytest
from decimal import Decimal
from django.utils import timezone
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.users.models import User
from apps.categories.models import Category
from apps.products.models import Product
from apps.cart.models import Cart, CartItem
from apps.orders.models import Order
from apps.orders.pricing import FIXED_CITY_DELIVERY_FEE


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username='orderuser',
        email='order@example.com',
        password='pass123',
    )


@pytest.fixture
def staff_user(db):
    return User.objects.create_user(
        username='stafforder',
        email='staff-order@example.com',
        password='pass123',
        is_staff=True,
    )


@pytest.fixture
def product(db):
    category = Category.objects.create(name='Tulips', slug='tulips')
    return Product.objects.create(
        name='Tulip Bouquet',
        description='Colorful tulips',
        price='19.99',
        category=category,
        stock=15,
        is_available=True,
    )


@pytest.fixture
def cart_with_item(db, user, product):
    cart = Cart.objects.create(user=user)
    CartItem.objects.create(cart=cart, product=product, quantity=2)
    return cart


def order_payload(**overrides):
    payload = {
        'shipping_address': '123 Flower Street, Garden City',
        'phone': '+1234567890',
        'delivery_address': '123 Flower Street, Garden City',
        'delivery_lat': '41.311081',
        'delivery_lng': '69.240562',
        'delivery_date': timezone.localdate().isoformat(),
        'delivery_time_slot': Order.DeliveryTimeSlot.MIDDAY,
        'recipient_name': 'Jane Recipient',
        'recipient_phone': '+998901234567',
        'gift_note': 'Happy birthday',
        'call_recipient_before_delivery': True,
        'notes': 'Please handle with care',
    }
    payload.update(overrides)
    return payload


@pytest.mark.django_db
class TestOrderCreation:
    def test_create_order_success(self, api_client, user, cart_with_item):
        api_client.force_authenticate(user=user)
        url = reverse('order-create')
        response = api_client.post(
            url,
            order_payload(),
            format='json',
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert Order.objects.filter(user=user).count() == 1
        assert response.data['total_price'] == '39.98'
        assert response.data['delivery_fee'] == '0.00'
        assert response.data['delivery_address'] == '123 Flower Street, Garden City'
        assert response.data['delivery_time_slot'] == Order.DeliveryTimeSlot.MIDDAY
        assert response.data['recipient_name'] == 'Jane Recipient'
        assert response.data['gift_note'] == 'Happy birthday'
        assert response.data['call_recipient_before_delivery'] is True
        assert response.data['payment_method'] == Order.PaymentMethod.CASH
        assert response.data['payment_method_display'] == 'Cash'
        assert response.data['status_timeline'][0]['id'] == Order.Status.PENDING
        assert response.data['status_timeline'][0]['active'] is True
        product = Product.objects.get(name='Tulip Bouquet')
        assert product.stock == 13

    def test_create_order_accepts_card_payment(self, api_client, user, cart_with_item):
        api_client.force_authenticate(user=user)
        response = api_client.post(
            reverse('order-create'),
            order_payload(payment_method=Order.PaymentMethod.CARD),
            format='json',
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['payment_method'] == Order.PaymentMethod.CARD
        assert response.data['payment_method_display'] == 'Card'

    def test_create_order_adds_fixed_delivery_fee_below_free_threshold(
        self, api_client, user, product
    ):
        Cart.objects.create(user=user)
        CartItem.objects.create(cart=user.cart, product=product, quantity=1)

        api_client.force_authenticate(user=user)
        response = api_client.post(
            reverse('order-create'),
            order_payload(),
            format='json',
        )

        expected_total = Decimal(product.price) + FIXED_CITY_DELIVERY_FEE
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['delivery_fee'] == f'{FIXED_CITY_DELIVERY_FEE:.2f}'
        assert response.data['total_price'] == f'{expected_total:.2f}'

    def test_create_order_rejects_invalid_payment_method(
        self, api_client, user, cart_with_item
    ):
        api_client.force_authenticate(user=user)
        response = api_client.post(
            reverse('order-create'),
            order_payload(payment_method='bitcoin'),
            format='json',
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_order_accepts_simple_delivery_payload_with_defaults(
        self, api_client, user, cart_with_item
    ):
        api_client.force_authenticate(user=user)
        response = api_client.post(
            reverse('order-create'),
            {'shipping_address': '123 Street', 'phone': '+1234567890'},
            format='json',
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['delivery_address'] == '123 Street'
        assert response.data['delivery_date'] == timezone.localdate().isoformat()
        assert response.data['delivery_time_slot'] == Order.DeliveryTimeSlot.MIDDAY
        assert response.data['recipient_name'] == user.username
        assert response.data['recipient_phone'] == '+1234567890'

    def test_create_order_empty_cart(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse('order-create')
        response = api_client.post(
            url,
            order_payload(),
            format='json',
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_order_rejects_cart_quantity_above_current_stock(
        self, api_client, user, product
    ):
        product.stock = 1
        product.save(update_fields=['stock'])
        cart = Cart.objects.create(user=user)
        CartItem.objects.create(cart=cart, product=product, quantity=2)

        api_client.force_authenticate(user=user)
        response = api_client.post(
            reverse('order-create'),
            order_payload(),
            format='json',
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Order.objects.filter(user=user).count() == 0
        product.refresh_from_db()
        assert product.stock == 1

    def test_order_list_returns_user_orders(self, api_client, user, cart_with_item):
        api_client.force_authenticate(user=user)
        api_client.post(
            reverse('order-create'),
            order_payload(),
            format='json',
        )
        response = api_client.get(reverse('order-list'))
        assert response.status_code == status.HTTP_200_OK
        # paginated response
        assert response.data['count'] == 1
        assert len(response.data['results']) == 1

    def test_staff_can_update_order_to_courier_picked_up(
        self, api_client, user, staff_user, cart_with_item
    ):
        api_client.force_authenticate(user=user)
        create_response = api_client.post(
            reverse('order-create'),
            order_payload(),
            format='json',
        )

        api_client.force_authenticate(user=staff_user)
        response = api_client.patch(
            reverse('order-status-update', args=[create_response.data['id']]),
            {'status': Order.Status.COURIER_PICKED_UP},
            format='json',
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == Order.Status.COURIER_PICKED_UP
        courier_step = response.data['status_timeline'][3]
        assert courier_step['active'] is True
        assert response.data['status_timeline'][2]['completed'] is True

    def test_order_requires_auth(self, api_client):
        response = api_client.post(reverse('order-create'), {})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
