import pytest
from decimal import Decimal
from unittest.mock import Mock, patch
from django.test import override_settings
from django.utils import timezone
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.users.models import User
from apps.categories.models import Category
from apps.products.models import Product
from apps.cart.models import Cart, CartItem
from apps.marketplace.models import Courier, PromoCode
from apps.orders import notifications
from apps.orders.models import DeliveryZone, NotificationLog, Order
from apps.orders.payment_providers import get_payment_provider
from apps.orders.payment_providers.test_provider import TestPaymentProvider
from apps.orders.pricing import FIXED_CITY_DELIVERY_FEE, OUTER_CITY_DELIVERY_FEE


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
def courier_user(db):
    return User.objects.create_user(
        username='courier',
        email='courier@example.com',
        password='pass123',
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
    @override_settings(PAYMENT_PROVIDER='test')
    def test_test_payment_provider_is_selected_by_default(self):
        provider = get_payment_provider()

        assert isinstance(provider, TestPaymentProvider)

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
        assert response.data['payment_status'] == Order.PaymentStatus.UNPAID
        assert response.data['payment_status_display'] == 'Unpaid'
        assert response.data['payment_provider'] == 'cash'
        assert response.data['payment_reference'] == ''
        assert response.data['paid_at'] is None
        assert response.data['status_timeline'][0]['id'] == Order.Status.PENDING
        assert response.data['status_timeline'][0]['active'] is True
        assert any(
            log['event'] == NotificationLog.Event.ORDER_CREATED
            and log['channel'] == NotificationLog.Channel.CONSOLE
            and log['status'] == NotificationLog.Status.SENT
            for log in response.data['notification_logs']
        )
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
        assert response.data['payment_status'] == Order.PaymentStatus.PENDING
        assert response.data['payment_provider'] == 'test'
        assert response.data['payment_reference'].startswith('TEST-')

    def test_create_order_accepts_online_payment(self, api_client, user, cart_with_item):
        api_client.force_authenticate(user=user)
        response = api_client.post(
            reverse('order-create'),
            order_payload(payment_method=Order.PaymentMethod.ONLINE),
            format='json',
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['payment_method'] == Order.PaymentMethod.ONLINE
        assert response.data['payment_status'] == Order.PaymentStatus.PENDING
        assert response.data['payment_provider'] == 'test'
        assert response.data['payment_reference'].startswith('TEST-')

    @override_settings(
        PAYMENT_PROVIDER='stripe',
        STRIPE_SECRET_KEY='',
        STRIPE_WEBHOOK_SECRET='',
    )
    def test_missing_real_provider_config_returns_clear_error(
        self, api_client, user, cart_with_item
    ):
        api_client.force_authenticate(user=user)
        response = api_client.post(
            reverse('order-create'),
            order_payload(payment_method=Order.PaymentMethod.CARD),
            format='json',
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'not configured' in str(response.data['payment_provider'])
        assert Order.objects.filter(user=user).count() == 0
        assert cart_with_item.items.count() == 1

    @override_settings(
        PAYMENT_PROVIDER='stripe',
        STRIPE_SECRET_KEY='',
        STRIPE_WEBHOOK_SECRET='',
    )
    def test_cash_order_does_not_require_configured_provider(
        self, api_client, user, cart_with_item
    ):
        api_client.force_authenticate(user=user)
        response = api_client.post(
            reverse('order-create'),
            order_payload(payment_method=Order.PaymentMethod.CASH),
            format='json',
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['payment_method'] == Order.PaymentMethod.CASH
        assert response.data['payment_status'] == Order.PaymentStatus.UNPAID
        assert response.data['payment_provider'] == 'cash'

    def test_owner_can_pay_test_order(self, api_client, user, cart_with_item):
        api_client.force_authenticate(user=user)
        create_response = api_client.post(
            reverse('order-create'),
            order_payload(payment_method=Order.PaymentMethod.CARD),
            format='json',
        )

        response = api_client.post(
            reverse('order-pay-test', args=[create_response.data['id']]),
            {},
            format='json',
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['payment_status'] == Order.PaymentStatus.PAID
        assert response.data['payment_provider'] == 'test'
        assert response.data['payment_reference'].startswith('TEST-')
        assert response.data['paid_at'] is not None

    def test_test_payment_changes_pending_order_to_paid(
        self, api_client, user, cart_with_item
    ):
        api_client.force_authenticate(user=user)
        create_response = api_client.post(
            reverse('order-create'),
            order_payload(payment_method=Order.PaymentMethod.ONLINE),
            format='json',
        )

        assert create_response.data['payment_status'] == Order.PaymentStatus.PENDING
        response = api_client.post(
            reverse('order-pay-test', args=[create_response.data['id']]),
            {},
            format='json',
        )

        order = Order.objects.get(pk=create_response.data['id'])
        assert response.status_code == status.HTTP_200_OK
        assert order.payment_status == Order.PaymentStatus.PAID
        assert order.paid_at is not None

    def test_another_customer_cannot_pay_someone_elses_order(
        self, api_client, user, cart_with_item
    ):
        other_user = User.objects.create_user(
            username='other-customer',
            email='other-customer@example.com',
            password='pass123',
        )
        api_client.force_authenticate(user=user)
        create_response = api_client.post(
            reverse('order-create'),
            order_payload(payment_method=Order.PaymentMethod.CARD),
            format='json',
        )

        api_client.force_authenticate(user=other_user)
        response = api_client.post(
            reverse('order-pay-test', args=[create_response.data['id']]),
            {},
            format='json',
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        order = Order.objects.get(pk=create_response.data['id'])
        assert order.payment_status == Order.PaymentStatus.PENDING
        assert order.paid_at is None

    def test_cash_order_does_not_use_test_payment(
        self, api_client, user, cart_with_item
    ):
        api_client.force_authenticate(user=user)
        create_response = api_client.post(
            reverse('order-create'),
            order_payload(payment_method=Order.PaymentMethod.CASH),
            format='json',
        )

        response = api_client.post(
            reverse('order-pay-test', args=[create_response.data['id']]),
            {},
            format='json',
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        order = Order.objects.get(pk=create_response.data['id'])
        assert order.payment_status == Order.PaymentStatus.UNPAID
        assert order.paid_at is None

    def test_create_order_applies_valid_promo_code(
        self, api_client, user, cart_with_item
    ):
        PromoCode.objects.create(
            code='SAVE5',
            discount_type=PromoCode.DiscountType.FIXED_AMOUNT,
            discount_value='5.00',
            min_order_amount='10.00',
        )

        api_client.force_authenticate(user=user)
        response = api_client.post(
            reverse('order-create'),
            order_payload(promo_code='save5'),
            format='json',
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['discount_amount'] == '5.00'
        assert response.data['total_price'] == '34.98'
        assert PromoCode.objects.get(code='SAVE5').used_count == 1

    def test_create_order_rejects_invalid_promo_code(
        self, api_client, user, cart_with_item
    ):
        api_client.force_authenticate(user=user)
        response = api_client.post(
            reverse('order-create'),
            order_payload(promo_code='missing'),
            format='json',
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Order.objects.filter(user=user).count() == 0

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

    def test_create_order_uses_selected_delivery_zone_fee(
        self, api_client, user, product
    ):
        zone = DeliveryZone.objects.get(name='Outer Tashkent')
        Cart.objects.create(user=user)
        CartItem.objects.create(cart=user.cart, product=product, quantity=1)

        api_client.force_authenticate(user=user)
        response = api_client.post(
            reverse('order-create'),
            order_payload(delivery_zone_id=zone.id),
            format='json',
        )

        expected_total = Decimal(product.price) + OUTER_CITY_DELIVERY_FEE
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['delivery_zone']['name'] == 'Outer Tashkent'
        assert response.data['delivery_zone']['city'] == 'Tashkent'
        assert response.data['delivery_fee'] == f'{OUTER_CITY_DELIVERY_FEE:.2f}'
        assert response.data['total_price'] == f'{expected_total:.2f}'

    def test_create_order_flags_manual_delivery_confirmation(
        self, api_client, user, product
    ):
        zone = DeliveryZone.objects.get(name='Outside City')
        Cart.objects.create(user=user)
        CartItem.objects.create(cart=user.cart, product=product, quantity=1)

        api_client.force_authenticate(user=user)
        response = api_client.post(
            reverse('order-create'),
            order_payload(delivery_zone_id=zone.id),
            format='json',
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['delivery_zone']['name'] == 'Outside City'
        assert response.data['delivery_requires_confirmation'] is True

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
        assert any(
            log['event'] == NotificationLog.Event.COURIER_PICKED_UP
            for log in response.data['notification_logs']
        )
        assert response.data['courier_picked_up_at'] is not None

    def test_staff_can_assign_courier(
        self, api_client, user, staff_user, courier_user, cart_with_item
    ):
        courier = Courier.objects.create(
            user=courier_user,
            phone='+998901111111',
            current_status=Courier.Status.AVAILABLE,
        )
        api_client.force_authenticate(user=user)
        create_response = api_client.post(
            reverse('order-create'),
            order_payload(),
            format='json',
        )

        api_client.force_authenticate(user=staff_user)
        response = api_client.patch(
            reverse('order-courier-assign', args=[create_response.data['id']]),
            {'courier_id': courier.id},
            format='json',
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['assigned_courier_id'] == courier.id
        assert response.data['courier_assigned_at'] is not None

    def test_delivered_order_awards_loyalty_points(
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
            {'status': Order.Status.DELIVERED},
            format='json',
        )

        user.refresh_from_db()
        assert response.status_code == status.HTTP_200_OK
        assert response.data['delivered_at'] is not None
        assert response.data['loyalty_points_earned'] > 0
        assert user.loyalty_points == response.data['loyalty_points_earned']

    def test_customer_can_repeat_order_to_cart(
        self, api_client, user, cart_with_item
    ):
        api_client.force_authenticate(user=user)
        create_response = api_client.post(
            reverse('order-create'),
            order_payload(),
            format='json',
        )

        response = api_client.post(
            reverse('order-repeat', args=[create_response.data['id']]),
            {},
            format='json',
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['cart']['total_items'] == 2
        assert response.data['skipped'] == []

    def test_staff_can_update_payment_status(self, api_client, user, staff_user, cart_with_item):
        api_client.force_authenticate(user=user)
        create_response = api_client.post(
            reverse('order-create'),
            order_payload(),
            format='json',
        )

        api_client.force_authenticate(user=staff_user)
        response = api_client.patch(
            reverse('order-payment-status-update', args=[create_response.data['id']]),
            {
                'payment_status': Order.PaymentStatus.PAID,
                'payment_provider': 'manual',
                'payment_reference': 'staff-receipt-001',
            },
            format='json',
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['payment_status'] == Order.PaymentStatus.PAID
        assert response.data['payment_provider'] == 'manual'
        assert response.data['payment_reference'] == 'staff-receipt-001'
        assert response.data['paid_at'] is not None
        assert any(
            log['event'] == NotificationLog.Event.PAYMENT_PAID
            for log in response.data['notification_logs']
        )

    def test_staff_can_mark_payment_failed(
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
            reverse('order-payment-status-update', args=[create_response.data['id']]),
            {'payment_status': Order.PaymentStatus.FAILED},
            format='json',
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['payment_status'] == Order.PaymentStatus.FAILED
        assert response.data['paid_at'] is None
        assert any(
            log['event'] == NotificationLog.Event.PAYMENT_FAILED
            for log in response.data['notification_logs']
        )

    def test_customer_cannot_update_payment_status(
        self, api_client, user, cart_with_item
    ):
        api_client.force_authenticate(user=user)
        create_response = api_client.post(
            reverse('order-create'),
            order_payload(),
            format='json',
        )

        response = api_client.patch(
            reverse('order-payment-status-update', args=[create_response.data['id']]),
            {'payment_status': Order.PaymentStatus.PAID},
            format='json',
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        order = Order.objects.get(pk=create_response.data['id'])
        assert order.payment_status == Order.PaymentStatus.UNPAID
        assert order.paid_at is None

    def test_rejects_unknown_payment_status(
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
            reverse('order-payment-status-update', args=[create_response.data['id']]),
            {'payment_status': 'captured'},
            format='json',
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_rejects_invalid_payment_status_transition(
        self, api_client, user, staff_user, cart_with_item
    ):
        api_client.force_authenticate(user=user)
        create_response = api_client.post(
            reverse('order-create'),
            order_payload(),
            format='json',
        )

        api_client.force_authenticate(user=staff_user)
        paid_response = api_client.patch(
            reverse('order-payment-status-update', args=[create_response.data['id']]),
            {'payment_status': Order.PaymentStatus.PAID},
            format='json',
        )
        failed_response = api_client.patch(
            reverse('order-payment-status-update', args=[create_response.data['id']]),
            {'payment_status': Order.PaymentStatus.FAILED},
            format='json',
        )

        assert paid_response.status_code == status.HTTP_200_OK
        assert failed_response.status_code == status.HTTP_400_BAD_REQUEST

    def test_staff_dashboard_returns_order_and_inventory_stats(
        self, api_client, user, staff_user, cart_with_item, product
    ):
        product.low_stock_threshold = 20
        product.save(update_fields=['low_stock_threshold'])
        api_client.force_authenticate(user=user)
        api_client.post(
            reverse('order-create'),
            order_payload(),
            format='json',
        )

        api_client.force_authenticate(user=staff_user)
        response = api_client.get(reverse('order-dashboard'))

        assert response.status_code == status.HTTP_200_OK
        assert response.data['today_orders'] == 1
        assert response.data['pending_orders'] == 1
        assert response.data['low_stock_products'][0]['name'] == product.name
        assert response.data['delivery_queue'][0]['id']

    def test_telegram_disabled_creates_skipped_log(
        self, settings, user, cart_with_item
    ):
        settings.NOTIFICATIONS_ENABLED = True
        settings.EMAIL_NOTIFICATIONS_ENABLED = False
        settings.TELEGRAM_NOTIFICATIONS_ENABLED = False
        settings.EMAIL_HOST_USER = ''
        settings.TELEGRAM_BOT_TOKEN = ''
        settings.TELEGRAM_ADMIN_CHAT_ID = ''
        order = Order.objects.create(
            user=user,
            total_price='10.00',
            shipping_address='123 Street',
            phone='+123456789',
        )

        logs = notifications.notify_order_created(order)

        console_log = next(
            log for log in logs if log.channel == NotificationLog.Channel.CONSOLE
        )
        telegram_log = next(
            log for log in logs if log.channel == NotificationLog.Channel.TELEGRAM
        )
        assert console_log.status == NotificationLog.Status.SENT
        assert console_log.event_type == NotificationLog.Event.ORDER_CREATED
        assert console_log.subject == f'Order #{order.id} created'
        assert console_log.recipient == user.email
        assert console_log.related_order == order
        assert console_log.sent_at is not None
        assert telegram_log.status == NotificationLog.Status.SKIPPED
        assert 'disabled' in telegram_log.error_message

    def test_order_creation_creates_email_notification_log(
        self, settings, api_client, user, cart_with_item
    ):
        settings.NOTIFICATIONS_ENABLED = True
        settings.EMAIL_NOTIFICATIONS_ENABLED = False
        settings.TELEGRAM_NOTIFICATIONS_ENABLED = False
        api_client.force_authenticate(user=user)

        response = api_client.post(
            reverse('order-create'),
            order_payload(),
            format='json',
        )

        assert response.status_code == status.HTTP_201_CREATED
        email_log = NotificationLog.objects.get(
            related_order_id=response.data['id'],
            event_type=NotificationLog.Event.ORDER_CREATED,
            channel=NotificationLog.Channel.EMAIL,
        )
        assert email_log.status == NotificationLog.Status.SKIPPED
        assert 'disabled' in email_log.error_message

    def test_email_disabled_creates_skipped_log(self, settings, user):
        settings.NOTIFICATIONS_ENABLED = True
        settings.EMAIL_NOTIFICATIONS_ENABLED = False
        settings.TELEGRAM_NOTIFICATIONS_ENABLED = False
        order = Order.objects.create(
            user=user,
            total_price='10.00',
            shipping_address='123 Street',
            phone='+123456789',
        )

        logs = notifications.notify_order_created(order)

        email_log = next(
            log for log in logs if log.channel == NotificationLog.Channel.EMAIL
        )
        assert email_log.status == NotificationLog.Status.SKIPPED
        assert 'disabled' in email_log.error_message

    def test_missing_customer_email_creates_skipped_log(self, settings, user):
        settings.NOTIFICATIONS_ENABLED = True
        settings.EMAIL_NOTIFICATIONS_ENABLED = True
        settings.TELEGRAM_NOTIFICATIONS_ENABLED = False
        settings.EMAIL_HOST = 'smtp.example.com'
        settings.EMAIL_HOST_USER = 'orders@example.com'
        settings.EMAIL_HOST_PASSWORD = 'fake-password'
        settings.DEFAULT_FROM_EMAIL = 'orders@example.com'
        order = Order.objects.create(
            user=user,
            total_price='10.00',
            shipping_address='123 Street',
            phone='+123456789',
        )
        order.user.email = ''

        logs = notifications.notify_order_created(order)

        email_log = next(
            log for log in logs if log.channel == NotificationLog.Channel.EMAIL
        )
        assert email_log.status == NotificationLog.Status.SKIPPED
        assert email_log.recipient == ''
        assert 'Customer email is missing' in email_log.error_message

    def test_successful_mocked_email_send_creates_sent_log(self, settings, user):
        settings.NOTIFICATIONS_ENABLED = True
        settings.EMAIL_NOTIFICATIONS_ENABLED = True
        settings.TELEGRAM_NOTIFICATIONS_ENABLED = False
        settings.EMAIL_HOST = 'smtp.example.com'
        settings.EMAIL_HOST_USER = 'orders@example.com'
        settings.EMAIL_HOST_PASSWORD = 'fake-password'
        settings.DEFAULT_FROM_EMAIL = 'orders@example.com'
        order = Order.objects.create(
            user=user,
            total_price='10.00',
            shipping_address='123 Street',
            phone='+123456789',
        )

        with patch('apps.orders.notification_services.send_mail', return_value=1) as send:
            logs = notifications.notify_order_created(order)

        email_log = next(
            log for log in logs if log.channel == NotificationLog.Channel.EMAIL
        )
        assert email_log.status == NotificationLog.Status.SENT
        assert email_log.recipient == user.email
        assert email_log.sent_at is not None
        assert email_log.subject == f'Bloom & Petal: Your order #{order.id} was created'
        assert 'Order status:' in email_log.message
        send.assert_called_once()
        assert send.call_args.args[3] == ['order@example.com']

    def test_failed_mocked_email_send_creates_failed_log(self, settings, user):
        settings.NOTIFICATIONS_ENABLED = True
        settings.EMAIL_NOTIFICATIONS_ENABLED = True
        settings.TELEGRAM_NOTIFICATIONS_ENABLED = False
        settings.EMAIL_HOST = 'smtp.example.com'
        settings.EMAIL_HOST_USER = 'orders@example.com'
        settings.EMAIL_HOST_PASSWORD = 'fake-password'
        settings.DEFAULT_FROM_EMAIL = 'orders@example.com'
        order = Order.objects.create(
            user=user,
            total_price='10.00',
            shipping_address='123 Street',
            phone='+123456789',
        )

        with patch(
            'apps.orders.notification_services.send_mail',
            side_effect=RuntimeError('SMTP unavailable'),
        ):
            logs = notifications.notify_order_created(order)

        email_log = next(
            log for log in logs if log.channel == NotificationLog.Channel.EMAIL
        )
        assert email_log.status == NotificationLog.Status.FAILED
        assert 'SMTP unavailable' in email_log.error_message

    def test_checkout_succeeds_if_email_sending_fails(
        self, settings, api_client, user, cart_with_item
    ):
        settings.NOTIFICATIONS_ENABLED = True
        settings.EMAIL_NOTIFICATIONS_ENABLED = True
        settings.TELEGRAM_NOTIFICATIONS_ENABLED = False
        settings.EMAIL_HOST = 'smtp.example.com'
        settings.EMAIL_HOST_USER = 'orders@example.com'
        settings.EMAIL_HOST_PASSWORD = 'fake-password'
        settings.DEFAULT_FROM_EMAIL = 'orders@example.com'
        api_client.force_authenticate(user=user)

        with patch(
            'apps.orders.notification_services.send_mail',
            side_effect=RuntimeError('SMTP unavailable'),
        ):
            response = api_client.post(
                reverse('order-create'),
                order_payload(),
                format='json',
            )

        assert response.status_code == status.HTTP_201_CREATED
        email_log = NotificationLog.objects.get(
            related_order_id=response.data['id'],
            event_type=NotificationLog.Event.ORDER_CREATED,
            channel=NotificationLog.Channel.EMAIL,
        )
        assert email_log.status == NotificationLog.Status.FAILED

    def test_successful_mocked_telegram_send_creates_sent_log(
        self, settings, user
    ):
        settings.NOTIFICATIONS_ENABLED = True
        settings.EMAIL_NOTIFICATIONS_ENABLED = False
        settings.TELEGRAM_NOTIFICATIONS_ENABLED = True
        settings.TELEGRAM_BOT_TOKEN = 'fake-token'
        settings.TELEGRAM_ADMIN_CHAT_ID = '123'
        order = Order.objects.create(
            user=user,
            total_price='10.00',
            shipping_address='123 Street',
            phone='+123456789',
        )
        response = Mock(status_code=200, text='{"ok": true}')
        response.json.return_value = {'ok': True, 'result': {'message_id': 1}}

        with patch('apps.orders.notification_services.requests.post', return_value=response) as post:
            logs = notifications.notify_order_created(order)

        telegram_log = next(
            log for log in logs if log.channel == NotificationLog.Channel.TELEGRAM
        )
        assert telegram_log.status == NotificationLog.Status.SENT
        assert telegram_log.recipient == '123'
        assert telegram_log.sent_at is not None
        assert 'New order' in telegram_log.message
        assert 'fake-token' not in telegram_log.error_message
        post.assert_called_once()
        request_payload = post.call_args.kwargs['json']
        assert request_payload['chat_id'] == '123'
        assert 'New order' in request_payload['text']

    def test_failed_mocked_telegram_send_creates_failed_log(
        self, settings, user
    ):
        settings.NOTIFICATIONS_ENABLED = True
        settings.EMAIL_NOTIFICATIONS_ENABLED = False
        settings.TELEGRAM_NOTIFICATIONS_ENABLED = True
        settings.TELEGRAM_BOT_TOKEN = 'fake-token'
        settings.TELEGRAM_ADMIN_CHAT_ID = '123'
        order = Order.objects.create(
            user=user,
            total_price='10.00',
            shipping_address='123 Street',
            phone='+123456789',
        )
        response = Mock(status_code=400, text='{"ok": false, "description": "bad request"}')
        response.json.return_value = {'ok': False, 'description': 'bad request'}

        with patch('apps.orders.notification_services.requests.post', return_value=response):
            logs = notifications.notify_order_created(order)

        telegram_log = next(
            log for log in logs if log.channel == NotificationLog.Channel.TELEGRAM
        )
        assert telegram_log.status == NotificationLog.Status.FAILED
        assert 'HTTP 400' in telegram_log.error_message
        assert 'fake-token' not in telegram_log.error_message

    def test_notification_service_skips_missing_credentials_without_crashing(
        self, settings, user
    ):
        settings.NOTIFICATIONS_ENABLED = True
        settings.EMAIL_NOTIFICATIONS_ENABLED = True
        settings.TELEGRAM_NOTIFICATIONS_ENABLED = True
        settings.EMAIL_HOST = ''
        settings.EMAIL_HOST_USER = ''
        settings.EMAIL_HOST_PASSWORD = ''
        settings.DEFAULT_FROM_EMAIL = ''
        settings.TELEGRAM_BOT_TOKEN = ''
        settings.TELEGRAM_ADMIN_CHAT_ID = ''
        order = Order.objects.create(
            user=user,
            total_price='10.00',
            shipping_address='123 Street',
            phone='+123456789',
        )

        logs = notifications.notify_order_created(order)

        assert {log.channel for log in logs} == {
            NotificationLog.Channel.CONSOLE,
            NotificationLog.Channel.EMAIL,
            NotificationLog.Channel.TELEGRAM,
        }
        assert [
            log.status for log in logs
            if log.channel in [NotificationLog.Channel.EMAIL, NotificationLog.Channel.TELEGRAM]
        ] == [NotificationLog.Status.SKIPPED, NotificationLog.Status.SKIPPED]

    def test_order_creation_triggers_telegram_notification_when_enabled(
        self, settings, api_client, user, cart_with_item
    ):
        settings.NOTIFICATIONS_ENABLED = True
        settings.EMAIL_NOTIFICATIONS_ENABLED = False
        settings.TELEGRAM_NOTIFICATIONS_ENABLED = True
        settings.TELEGRAM_BOT_TOKEN = 'fake-token'
        settings.TELEGRAM_ADMIN_CHAT_ID = '123'
        response = Mock(status_code=200, text='{"ok": true}')
        response.json.return_value = {'ok': True, 'result': {'message_id': 1}}

        api_client.force_authenticate(user=user)
        with patch('apps.orders.notification_services.requests.post', return_value=response) as post:
            create_response = api_client.post(
                reverse('order-create'),
                order_payload(),
                format='json',
            )

        assert create_response.status_code == status.HTTP_201_CREATED
        order = Order.objects.get(pk=create_response.data['id'])
        telegram_log = NotificationLog.objects.get(
            related_order=order,
            event_type=NotificationLog.Event.ORDER_CREATED,
            channel=NotificationLog.Channel.TELEGRAM,
        )
        assert telegram_log.status == NotificationLog.Status.SENT
        assert 'New order' in telegram_log.message
        assert 'Recipient: Jane Recipient' in telegram_log.message
        post.assert_called_once()

    def test_disabled_notifications_are_skipped_cleanly(self, settings, user):
        settings.NOTIFICATIONS_ENABLED = False
        order = Order.objects.create(
            user=user,
            total_price='10.00',
            shipping_address='123 Street',
            phone='+123456789',
        )

        logs = notifications.notify_order_created(order)

        assert len(logs) == 1
        assert logs[0].channel == NotificationLog.Channel.CONSOLE
        assert logs[0].status == NotificationLog.Status.SKIPPED
        assert 'disabled' in logs[0].error_message

    def test_order_requires_auth(self, api_client):
        response = api_client.post(reverse('order-create'), {})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
