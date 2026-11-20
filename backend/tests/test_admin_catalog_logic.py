import pytest
from django.contrib.admin.sites import AdminSite
from django.urls import reverse

from apps.categories.admin import CategoryAdmin
from apps.categories.models import Category
from apps.marketplace.admin import CityAdmin, PromoCodeAdmin, VendorAdmin
from apps.marketplace.models import City, PromoCode, Vendor
from apps.products.admin import ProductAdmin
from apps.products.models import Product
from apps.users.models import User


@pytest.fixture
def admin_request(rf):
    request = rf.get('/admin/')
    request.user = User(is_staff=True, is_superuser=True, is_active=True)
    return request


@pytest.mark.django_db
@pytest.mark.parametrize(
    'model,admin_class,extra',
    [
        (
            Product,
            ProductAdmin,
            {'description': 'Flowers', 'price': '25.00', 'stock': 3, 'low_stock_threshold': 3},
        ),
        (Category, CategoryAdmin, {}),
        (
            City,
            CityAdmin,
            {
                'country': 'Uzbekistan',
                'currency': 'UZS',
                'default_delivery_fee': '2.00',
                'free_delivery_threshold': '40.00',
            },
        ),
        (Vendor, VendorAdmin, {'commission_percent': '10.00'}),
    ],
)
def test_admin_checks_generated_slug_before_saving(admin_request, model, admin_class, extra):
    model.objects.create(name='Existing entry', slug='same-name', **extra)
    form_class = admin_class(model, AdminSite()).get_form(admin_request)
    form = form_class(data={'name': 'Same name', 'slug': '', **extra})
    assert not form.is_valid()
    assert 'slug' in form.errors


@pytest.mark.django_db
@pytest.mark.parametrize('name', ['R' * 60, '\U0001f337\U0001f33b'])
def test_admin_rejects_an_invalid_generated_slug(admin_request, name):
    form = CategoryAdmin(Category, AdminSite()).get_form(admin_request)(
        data={'name': name, 'slug': ''}
    )
    assert not form.is_valid()
    assert 'slug' in form.errors


def promo_form_data(code):
    return {
        'code': code,
        'discount_type': 'percent',
        'discount_value': '10.00',
        'min_order_amount': '0.00',
        'is_active': 'on',
        'valid_from_0': '2026-01-01',
        'valid_from_1': '00:00:00',
    }


@pytest.mark.django_db
def test_admin_rejects_duplicate_promo_after_normalizing_case(admin_request):
    PromoCode.objects.create(code='SPRING10', discount_type='percent', discount_value='10.00')
    form = PromoCodeAdmin(PromoCode, AdminSite()).get_form(admin_request)(
        data=promo_form_data('spring10')
    )
    assert not form.is_valid()
    assert 'code' in form.errors


@pytest.mark.django_db
def test_admin_can_keep_current_promo_with_different_case(admin_request):
    promo = PromoCode.objects.create(
        code='SPRING10', discount_type='percent', discount_value='10.00'
    )
    form = PromoCodeAdmin(PromoCode, AdminSite()).get_form(admin_request, promo)(
        instance=promo, data=promo_form_data('spring10')
    )
    assert form.is_valid(), form.errors
    assert form.save().code == 'SPRING10'


@pytest.mark.django_db
def test_generated_duplicate_slug_post_returns_validation_instead_of_crashing(client):
    staff = User.objects.create_superuser(
        username='category-admin', email='category@example.test', password='test-only-password'
    )
    Category.objects.create(name='Existing category', slug='garden-flowers')
    client.force_login(staff)
    response = client.post(
        reverse('admin:categories_category_add'), {'name': 'Garden flowers', 'slug': ''}
    )
    assert response.status_code == 200
    assert 'slug' in response.context['adminform'].form.errors
    assert not Category.objects.filter(name='Garden flowers').exists()
