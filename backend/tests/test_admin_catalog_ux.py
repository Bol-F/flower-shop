from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest
from apps.marketplace.admin import CityAdmin, PromoAvailabilityFilter, PromoCodeAdmin
from apps.marketplace.models import City, PromoCode
from apps.marketplace.services import validate_promo_code
from apps.products.admin import ProductAdmin, StockLevelFilter
from apps.products.models import Product
from apps.users.models import User
from django.contrib.admin.sites import AdminSite
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils import timezone
from rest_framework.exceptions import ValidationError as APIValidationError
from rest_framework.test import APIClient


@pytest.mark.django_db
@pytest.mark.parametrize(
    'stock_level, expected_names',
    [
        ('low', {'Sold out roses', 'Last tulips', 'Threshold lilies', 'Large threshold'}),
        ('in_stock', {'Plentiful peonies'}),
        ('out_of_stock', {'Sold out roses', 'Hidden sold out'}),
    ],
)
def test_stock_filter_uses_each_products_threshold(rf, stock_level, expected_names):
    for name, stock, threshold, available in (
        ('Sold out roses', 0, 3, True),
        ('Last tulips', 2, 3, True),
        ('Threshold lilies', 8, 8, True),
        ('Large threshold', 10, 15, True),
        ('Plentiful peonies', 4, 3, True),
        ('Hidden sold out', 0, 3, False),
        ('Hidden low stock', 1, 3, False),
        ('Hidden plentiful', 20, 3, False),
    ):
        Product.objects.create(
            name=name,
            price='100.00',
            stock=stock,
            low_stock_threshold=threshold,
            is_available=available,
        )

    request = rf.get('/admin/products/product/', {'stock_level': stock_level})
    product_admin = ProductAdmin(Product, AdminSite())
    stock_filter = StockLevelFilter(request, {'stock_level': stock_level}, Product, product_admin)
    filtered = stock_filter.queryset(request, Product.objects.all())

    assert set(filtered.values_list('name', flat=True)) == expected_names


@pytest.mark.django_db
def test_product_price_is_validated_in_admin_api_and_database(rf):
    staff = User.objects.create_superuser(
        username='pricing-admin', email='pricing@example.com', password='pass123'
    )
    request = rf.get('/admin/products/product/add/')
    request.user = staff
    form_class = ProductAdmin(Product, AdminSite()).get_form(request)
    form = form_class(
        data={'name': 'Impossible roses', 'description': 'Bad price', 'price': '-5.00', 'stock': 5}
    )
    assert not form.is_valid()
    assert 'price' in form.errors

    client = APIClient()
    client.force_authenticate(user=staff)
    response = client.post(
        reverse('product-list'),
        {'name': 'Impossible roses', 'description': 'Bad price', 'price': '-5.00', 'stock': 5},
        format='json',
    )
    assert response.status_code == 400
    assert 'price' in response.data

    with pytest.raises(IntegrityError), transaction.atomic():
        Product.objects.create(name='Direct bad price', description='Bad price', price='-5.00')


@pytest.mark.django_db
@pytest.mark.parametrize(
    'fee,threshold,invalid_field',
    [('-1.00', '10.00', 'default_delivery_fee'), ('1.00', '-10.00', 'free_delivery_threshold')],
)
def test_city_delivery_configuration_cannot_be_negative(rf, fee, threshold, invalid_field):
    staff = User.objects.create_superuser(
        username='city-admin', email='city@example.com', password='pass123'
    )
    request = rf.get('/admin/marketplace/city/add/')
    request.user = staff
    form_class = CityAdmin(City, AdminSite()).get_form(request)
    form = form_class(
        data={
            'name': 'Sample City',
            'country': 'Uzbekistan',
            'currency': 'UZS',
            'default_delivery_fee': fee,
            'free_delivery_threshold': threshold,
            'is_active': 'on',
        }
    )
    assert not form.is_valid()
    assert invalid_field in form.errors

    with pytest.raises(IntegrityError), transaction.atomic():
        City.objects.create(
            name='Direct Bad City',
            default_delivery_fee=fee,
            free_delivery_threshold=threshold,
        )


@pytest.mark.django_db
def test_bulk_product_visibility_updates_only_changed_rows(client):
    staff = User.objects.create_superuser(
        username='catalog-admin', email='catalog@example.com', password='pass123'
    )
    visible = Product.objects.create(name='Visible roses', description='Roses', price='15.00')
    hidden = Product.objects.create(
        name='Hidden lilies', description='Lilies', price='18.00', is_available=False
    )
    initial_visible_update = visible.updated_at
    client.force_login(staff)
    response = client.post(
        '/admin/products/product/',
        {
            'action': 'publish_selected',
            '_selected_action': [str(visible.pk), str(hidden.pk)],
            'select_across': '0',
            'index': '0',
        },
    )
    assert response.status_code == 302
    visible.refresh_from_db()
    hidden.refresh_from_db()
    assert visible.is_available and hidden.is_available
    assert visible.updated_at == initial_visible_update

    response = client.post(
        '/admin/products/product/',
        {
            'action': 'hide_selected',
            '_selected_action': [str(visible.pk), str(hidden.pk)],
            'select_across': '0',
            'index': '0',
        },
    )
    assert response.status_code == 302
    visible.refresh_from_db()
    hidden.refresh_from_db()
    assert not visible.is_available and not hidden.is_available


@pytest.mark.django_db
@pytest.mark.parametrize(
    'discount_type,discount_value,min_amount,end_before_start,invalid_field',
    [
        ('percent', '101.00', '0.00', False, 'discount_value'),
        ('fixed_amount', '-1.00', '0.00', False, 'discount_value'),
        ('fixed_amount', '5.00', '-1.00', False, 'min_order_amount'),
        ('fixed_amount', '5.00', '0.00', True, 'valid_until'),
    ],
)
def test_promo_admin_rejects_invalid_business_configuration(
    rf, discount_type, discount_value, min_amount, end_before_start, invalid_field
):
    staff = User.objects.create_superuser(
        username='promo-admin', email='promo@example.com', password='pass123'
    )
    request = rf.get('/admin/marketplace/promocode/add/')
    request.user = staff
    form_class = PromoCodeAdmin(PromoCode, AdminSite()).get_form(request)
    assert 'used_count' not in form_class.base_fields
    start = timezone.now()
    end = start - timedelta(days=1) if end_before_start else start + timedelta(days=1)
    form = form_class(
        data={
            'code': 'BADPROMO',
            'discount_type': discount_type,
            'discount_value': discount_value,
            'min_order_amount': min_amount,
            'valid_from_0': start.date().isoformat(),
            'valid_from_1': start.time().strftime('%H:%M:%S'),
            'valid_until_0': end.date().isoformat(),
            'valid_until_1': end.time().strftime('%H:%M:%S'),
            'is_active': 'on',
            'used_count': '999',
        }
    )
    assert not form.is_valid()
    assert invalid_field in form.errors


@pytest.mark.django_db
def test_promo_database_rejects_negative_and_over_100_percent():
    for code, kind, amount in (
        ('NEGATIVE', PromoCode.DiscountType.FIXED_AMOUNT, '-1.00'),
        ('OVER100', PromoCode.DiscountType.PERCENT, '101.00'),
    ):
        with pytest.raises(IntegrityError), transaction.atomic():
            PromoCode.objects.create(code=code, discount_type=kind, discount_value=amount)


@pytest.mark.django_db
def test_promo_service_rejects_legacy_malformed_row():
    promo = PromoCode.objects.create(
        code='VALID',
        discount_type=PromoCode.DiscountType.FIXED_AMOUNT,
        discount_value=Decimal('5.00'),
    )
    promo.discount_value = Decimal('-5.00')
    with (
        patch.object(PromoCode.objects, 'get', return_value=promo),
        pytest.raises(APIValidationError),
    ):
        validate_promo_code('VALID', Decimal('40.00'))


@pytest.mark.django_db
def test_promo_filter_distinguishes_usable_and_expired(rf):
    now = timezone.now()
    for code, active, start, end, limit, used in (
        ('READY', True, now - timedelta(days=1), None, None, 0),
        ('WAITING', True, now + timedelta(days=1), None, None, 0),
        ('OLD', True, now - timedelta(days=2), now - timedelta(days=1), None, 0),
        ('USED', True, now - timedelta(days=1), None, 1, 1),
        ('OFF', False, now - timedelta(days=1), None, None, 0),
    ):
        PromoCode.objects.create(
            code=code,
            discount_type=PromoCode.DiscountType.PERCENT,
            discount_value='10.00',
            is_active=active,
            valid_from=start,
            valid_until=end,
            usage_limit=limit,
            used_count=used,
        )
    model_admin = PromoCodeAdmin(PromoCode, AdminSite())
    for availability, expected in (
        ('available', 'READY'),
        ('scheduled', 'WAITING'),
        ('expired', 'OLD'),
        ('exhausted', 'USED'),
        ('disabled', 'OFF'),
    ):
        request = rf.get('/admin/marketplace/promocode/', {'availability': availability})
        filter_instance = PromoAvailabilityFilter(
            request, {'availability': availability}, PromoCode, model_admin
        )
        filtered = filter_instance.queryset(request, PromoCode.objects.all())
        assert list(filtered.values_list('code', flat=True)) == [expected]
