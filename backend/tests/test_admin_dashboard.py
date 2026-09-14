"""The dashboard must reveal only the records available in the admin itself."""

from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch
from urllib.parse import urlsplit

import pytest
from apps.orders.models import Order
from apps.products.models import Product
from apps.users.templatetags.flower_admin import flower_dashboard, flower_navigation
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, Permission
from django.test import RequestFactory
from django.utils import timezone, translation


@pytest.fixture(autouse=True)
def default_dashboard_language():
    # LocaleMiddleware activates a language for each request; isolate these tests.
    with translation.override('en-us'):
        yield


def dashboard_for(user):
    request = RequestFactory().get('/admin/')
    request.user = user
    return flower_dashboard({'request': request})


def permit(user, *permissions):
    for app_label, codename in permissions:
        user.user_permissions.add(
            Permission.objects.get(content_type__app_label=app_label, codename=codename)
        )


@pytest.fixture
def staff(db):
    return get_user_model().objects.create_user(
        username='flower-staff', email='staff@example.test', password='test', is_staff=True
    )


@pytest.fixture
def customer(db):
    return get_user_model().objects.create_user(
        username='flower-customer', email='customer@example.test', password='test'
    )


def make_order(user, **kwargs):
    return Order.objects.create(
        user=user,
        total_price=Decimal('125000.00'),
        shipping_address='Flower Street 12',
        phone='+998900000000',
        **kwargs,
    )


def make_product(name, **kwargs):
    return Product.objects.create(name=name, price=Decimal('25000.00'), **kwargs)


@pytest.mark.django_db
class TestFlowerDashboardPermissions:
    def test_missing_request_does_not_disclose_data(self):
        assert flower_dashboard({})['cards'] == []

    def test_anonymous_and_nonstaff_do_not_disclose_data(self, customer):
        for user in (AnonymousUser(), customer):
            dashboard = dashboard_for(user)
            assert dashboard['cards'] == []
            assert dashboard['recent_orders'] == []
            assert dashboard['stock_items'] == []
            assert dashboard['urls'] == {}

    def test_inactive_staff_does_not_disclose_data(self, staff):
        staff.is_active = False
        staff.is_superuser = True
        assert dashboard_for(staff)['urls'] == {}

    def test_staff_without_permissions_sees_no_data(self, staff, customer):
        make_order(customer)
        make_product('Private roses')
        dashboard = dashboard_for(staff)
        assert dashboard['cards'] == []
        assert dashboard['recent_orders'] == []
        assert dashboard['stock_items'] == []
        assert dashboard['urls'] == {}

    def test_order_view_permission_only_exposes_orders(self, staff, customer):
        permit(staff, ('orders', 'view_order'))
        make_order(customer)
        make_product('Private roses')
        dashboard = dashboard_for(staff)
        assert len(dashboard['cards']) == 2
        assert len(dashboard['recent_orders']) == 1
        assert dashboard['stock_items'] == []
        assert set(dashboard['urls']) == {'orders', 'delivery_map'}

    def test_product_view_permission_does_not_offer_add(self, staff):
        permit(staff, ('products', 'view_product'))
        dashboard = dashboard_for(staff)
        assert len(dashboard['cards']) == 2
        assert set(dashboard['urls']) == {'products', 'stock'}

    def test_product_add_link_requires_add_permission(self, staff):
        permit(staff, ('products', 'view_product'), ('products', 'add_product'))
        assert dashboard_for(staff)['urls']['add_product'].endswith('/products/product/add/')

    def test_support_link_requires_message_permission(self, staff):
        permit(staff, ('contact', 'view_usermessage'))
        assert set(dashboard_for(staff)['urls']) == {'messages'}

    def test_registered_queryset_restrictions_apply_to_all_dashboard_data(self, staff, customer):
        permit(staff, ('orders', 'view_order'), ('products', 'view_product'))
        allowed_order = make_order(customer, delivery_date=timezone.localdate())
        make_order(customer, delivery_date=timezone.localdate())
        allowed_product = make_product('Visible roses', stock=1)
        make_product('Hidden roses', stock=0)

        with (
            patch.object(
                admin.site._registry[Order],
                'get_queryset',
                return_value=Order.objects.filter(pk=allowed_order.pk),
            ),
            patch.object(
                admin.site._registry[Product],
                'get_queryset',
                return_value=Product.objects.filter(pk=allowed_product.pk),
            ),
        ):
            dashboard = dashboard_for(staff)

        assert [card['value'] for card in dashboard['cards']] == [1, 1, 1, 1]
        assert [order['label'] for order in dashboard['recent_orders']] == [
            f'Order #{allowed_order.pk}'
        ]
        assert [product['name'] for product in dashboard['stock_items']] == ['Visible roses']


@pytest.mark.django_db
class TestFlowerDashboardData:
    def test_app_landing_still_lists_its_own_models(self, staff, client):
        permit(staff, ('products', 'view_product'))
        client.force_login(staff)
        response = client.get('/admin/products/')
        assert response.status_code == 200
        assert 'admin/app_index.html' in [template.name for template in response.templates]
        assert 'class="flower-stats"' not in response.content.decode()
        assert '/admin/products/product/' in response.content.decode()

    @pytest.mark.parametrize(
        'language,login_title,overview,orders_label,stock_label',
        [
            (
                'ru',
                'Добро пожаловать в цветочный магазин',
                'Обзор магазина',
                'Новые заказы',
                'Осталось: 0',
            ),
            (
                'uz',
                'Gul do‘koniga xush kelibsiz',
                'Do‘kon holati',
                'Yangi buyurtmalar',
                '0 ta qoldi',
            ),
        ],
    )
    def test_localized_workspace_and_login(
        self, staff, client, language, login_title, overview, orders_label, stock_label
    ):
        login_response = client.get(f'/{language}/admin/login/')
        assert login_response.status_code == 200
        assert login_title in login_response.content.decode()

        permit(staff, ('orders', 'view_order'), ('products', 'view_product'))
        make_product('Roses', stock=0)
        client.force_login(staff)
        response = client.get(f'/{language}/admin/')
        assert response.status_code == 200
        body = response.content.decode()
        assert overview in body
        assert orders_label in body
        assert stock_label in body

    def test_counts_and_links_match_real_records(self, staff, customer, client):
        permit(staff, ('orders', 'view_order'), ('products', 'view_product'))
        today = timezone.localdate()
        make_order(customer, delivery_date=today)
        make_order(customer, delivery_date=today, status=Order.Status.CONFIRMED)
        make_order(customer, delivery_date=today, status=Order.Status.CANCELLED)
        make_order(customer, delivery_date=today + timedelta(days=1))
        make_product('Zero stock', stock=0)
        make_product('At alert level', stock=3, low_stock_threshold=3)
        make_product('Healthy stock', stock=4, low_stock_threshold=3)
        make_product('Not on sale', stock=0, is_available=False)

        dashboard = dashboard_for(staff)
        assert [card['value'] for card in dashboard['cards']] == [2, 2, 3, 2]
        assert [item['name'] for item in dashboard['stock_items']] == [
            'Zero stock',
            'At alert level',
        ]
        client.force_login(staff)
        for card in dashboard['cards']:
            response = client.get(card['url'])
            assert response.status_code == 200
            assert response.context['cl'].result_count == card['value']

    def test_latest_orders_are_limited_to_five(self, staff, customer):
        permit(staff, ('orders', 'view_order'))
        orders = [make_order(customer) for _ in range(7)]
        dashboard = dashboard_for(staff)
        assert len(dashboard['recent_orders']) == 5
        assert [item['label'] for item in dashboard['recent_orders']] == [
            f'Order #{order.pk}' for order in reversed(orders[-5:])
        ]

    @pytest.mark.parametrize(
        'language,prefix',
        [('en-us', '/admin/'), ('en', '/en/admin/'), ('ru', '/ru/admin/'), ('uz', '/uz/admin/')],
    )
    def test_links_respect_active_language(self, staff, customer, language, prefix):
        permit(
            staff,
            ('orders', 'view_order'),
            ('products', 'view_product'),
            ('products', 'add_product'),
            ('users', 'view_user'),
        )
        make_order(customer)
        make_product('Roses')
        with translation.override(language):
            dashboard = dashboard_for(staff)
        urls = list(dashboard['urls'].values())
        urls += [card['url'] for card in dashboard['cards']]
        urls += [order['url'] for order in dashboard['recent_orders']]
        urls += [product['url'] for product in dashboard['stock_items']]
        assert all(urlsplit(url).path.startswith(prefix) for url in urls)


class TestFlowerNavigation:
    def test_preserves_each_permitted_model_once_without_mutating_input(self):
        apps = [
            {
                'name': name,
                'app_label': app_label,
                'models': [
                    {'name': model, 'object_name': model, 'admin_url': f'/{app_label}/{model}/'}
                    for model in models
                ],
            }
            for name, app_label, models in [
                ('Authentication', 'auth', ['Group']),
                ('Users', 'users', ['SocialIdentity', 'User']),
                ('Products', 'products', ['Product']),
                (
                    'Orders',
                    'orders',
                    ['NotificationLog', 'Order', 'PaymentAttempt', 'DeliveryZone', 'PaymentEvent'],
                ),
                ('Categories', 'categories', ['Category']),
                ('Future app', 'future', ['NewModel']),
            ]
        ]
        navigation = flower_navigation(apps)
        items = [item for group in navigation for item in group['items']]
        original_urls = [model['admin_url'] for app in apps for model in app['models']]
        assert sorted(item['admin_url'] for item in items) == sorted(original_urls)
        assert len(items) == len(original_urls)
        assert [item['object_name'] for item in navigation[0]['items']] == [
            'Order',
            'Product',
            'Category',
            'DeliveryZone',
        ]
        assert str(navigation[-1]['label']) == 'System'
        assert {item['object_name'] for item in navigation[-1]['items']} == {
            'Group',
            'NewModel',
            'PaymentAttempt',
            'PaymentEvent',
            'NotificationLog',
        }
        assert all('icon' not in model for app in apps for model in app['models'])

    def test_empty_navigation_has_no_empty_sections(self):
        assert flower_navigation([]) == []
