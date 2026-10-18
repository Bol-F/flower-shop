"""Staff is an admin-site flag, not permission to manage every shop resource."""

import pytest
from django.contrib.auth.models import Permission
from django.urls import reverse
from rest_framework.test import APIClient

from apps.categories.models import Category
from apps.contact.models import UserMessage
from apps.marketplace.models import Courier
from apps.products.models import Product
from apps.users.models import User


def grant(user, *permissions):
    for name in permissions:
        app_label, codename = name.split('.')
        user.user_permissions.add(
            Permission.objects.get(content_type__app_label=app_label, codename=codename)
        )
    return User.objects.get(pk=user.pk)


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def staff(db):
    return User.objects.create_user('staff', 'staff@example.test', 'password', is_staff=True)


@pytest.fixture
def customer(db):
    return User.objects.create_user('customer', 'customer@example.test', 'password')


@pytest.fixture
def category(db):
    return Category.objects.create(name='Roses', slug='roses', description='Original')


@pytest.fixture
def product(category):
    return Product.objects.create(
        name='Bouquet', price='25.00', stock=5, description='Original', category=category
    )


@pytest.fixture
def message(customer):
    return UserMessage.objects.create(
        user=customer, subject='Private question', body='Private body'
    )


WRITE_CASES = (
    ('product', 'post', 'add'),
    ('product', 'put', 'change'),
    ('product', 'patch', 'change'),
    ('product', 'delete', 'delete'),
    ('category', 'post', 'add'),
    ('category', 'put', 'change'),
    ('category', 'patch', 'change'),
    ('category', 'delete', 'delete'),
)


def write_resource(client, resource, method, product, category):
    obj = product if resource == 'product' else category
    url = (
        reverse(f'{resource}-list')
        if method == 'post'
        else reverse(f'{resource}-detail', kwargs={'slug': obj.slug})
    )
    payload = {'name': 'New entry' if method == 'post' else obj.name, 'description': 'Updated'}
    if resource == 'product':
        payload.update(price='30.00', stock=7, category_id=category.pk)
    return getattr(client, method)(url, payload, format='json')


@pytest.mark.django_db
class TestCatalogModelPermissions:
    @pytest.mark.parametrize('resource,method,action', WRITE_CASES)
    @pytest.mark.parametrize('role', ['no_permissions', 'view_only', 'unrelated_permission'])
    def test_staff_flag_or_read_permission_cannot_write_catalog(
        self, client, staff, category, product, resource, method, action, role
    ):
        app_label = 'products' if resource == 'product' else 'categories'
        if role == 'view_only':
            staff = grant(staff, f'{app_label}.view_{resource}')
        elif role == 'unrelated_permission':
            staff = grant(staff, 'orders.change_order')
        client.force_authenticate(staff)

        assert write_resource(client, resource, method, product, category).status_code == 403
        assert Category.objects.count() == 1
        assert Product.objects.count() == 1
        product.refresh_from_db()
        category.refresh_from_db()
        assert product.stock == 5
        assert product.description == 'Original'
        assert category.description == 'Original'

    @pytest.mark.parametrize('resource,method,action', WRITE_CASES)
    def test_exact_write_permission_is_sufficient_for_staff(
        self, client, staff, category, product, resource, method, action
    ):
        app_label = 'products' if resource == 'product' else 'categories'
        client.force_authenticate(grant(staff, f'{app_label}.{action}_{resource}'))
        expected = {'post': 201, 'put': 200, 'patch': 200, 'delete': 204}[method]
        assert write_resource(client, resource, method, product, category).status_code == expected

    @pytest.mark.parametrize('resource,method,action', WRITE_CASES)
    def test_non_staff_write_permissions_do_not_open_staff_api(
        self, client, customer, category, product, resource, method, action
    ):
        app_label = 'products' if resource == 'product' else 'categories'
        client.force_authenticate(grant(customer, f'{app_label}.{action}_{resource}'))
        assert write_resource(client, resource, method, product, category).status_code == 403

    @pytest.mark.parametrize(
        'role,visible',
        [
            ('anonymous', False),
            ('staff_no_permissions', False),
            ('non_staff_viewer', False),
            ('unrelated_staff', False),
            ('staff_viewer', True),
            ('superuser', True),
        ],
    )
    def test_unpublished_products_need_staff_product_view_permission(
        self, client, staff, customer, product, role, visible
    ):
        product.is_available = False
        product.save(update_fields=['is_available'])
        if role == 'staff_no_permissions':
            client.force_authenticate(staff)
        elif role == 'non_staff_viewer':
            client.force_authenticate(grant(customer, 'products.view_product'))
        elif role == 'unrelated_staff':
            client.force_authenticate(grant(staff, 'categories.view_category'))
        elif role == 'staff_viewer':
            client.force_authenticate(grant(staff, 'products.view_product'))
        elif role == 'superuser':
            client.force_authenticate(
                User.objects.create_superuser('owner', 'owner@example.test', 'password')
            )

        response = client.get(reverse('product-list'))
        assert response.status_code == 200
        assert response.data['count'] == (1 if visible else 0)
        detail = client.get(reverse('product-detail', kwargs={'slug': product.slug}))
        assert detail.status_code == (200 if visible else 404)

    def test_inventory_editor_can_update_an_unpublished_product(self, client, staff, product):
        product.is_available = False
        product.save(update_fields=['is_available'])
        client.force_authenticate(grant(staff, 'products.view_product', 'products.change_product'))
        response = client.patch(
            reverse('product-detail', kwargs={'slug': product.slug}), {'stock': 8}, format='json'
        )
        assert response.status_code == 200
        product.refresh_from_db()
        assert product.stock == 8


@pytest.mark.django_db
class TestSupportAndCourierPermissions:
    def test_staff_without_support_permissions_cannot_read_or_mark_read(
        self, client, staff, message
    ):
        client.force_authenticate(staff)
        assert client.get(reverse('contact-admin-list')).status_code == 403
        assert client.get(reverse('contact-admin-detail', args=[message.pk])).status_code == 403
        assert (
            client.patch(
                reverse('contact-admin-detail', args=[message.pk]),
                {'admin_reply': 'Unauthorized', 'is_read': True},
                format='json',
            ).status_code
            == 403
        )
        assert (
            client.post(
                reverse('contact-admin-reply', args=[message.pk]),
                {'body': 'Unauthorized'},
                format='json',
            ).status_code
            == 403
        )
        message.refresh_from_db()
        assert message.is_read is False
        assert not message.admin_reply
        assert message.replied_at is None
        assert UserMessage.objects.count() == 1

    def test_support_viewer_can_read_without_marking_or_replying(self, client, staff, message):
        client.force_authenticate(grant(staff, 'contact.view_usermessage'))
        assert client.get(reverse('contact-admin-list')).data['count'] == 1
        assert client.get(reverse('contact-admin-detail', args=[message.pk])).status_code == 200
        assert (
            client.patch(
                reverse('contact-admin-detail', args=[message.pk]), {'is_read': True}, format='json'
            ).status_code
            == 403
        )
        assert (
            client.post(
                reverse('contact-admin-reply', args=[message.pk]), {'body': 'No'}, format='json'
            ).status_code
            == 403
        )
        message.refresh_from_db()
        assert message.is_read is False
        assert UserMessage.objects.count() == 1

    def test_support_editor_can_reply_and_mark_read(self, client, staff, message):
        client.force_authenticate(
            grant(staff, 'contact.view_usermessage', 'contact.change_usermessage')
        )
        assert client.get(reverse('contact-admin-detail', args=[message.pk])).status_code == 200
        message.refresh_from_db()
        assert message.is_read is True
        assert (
            client.patch(
                reverse('contact-admin-detail', args=[message.pk]),
                {'admin_reply': 'Here to help'},
                format='json',
            ).status_code
            == 200
        )
        assert (
            client.post(
                reverse('contact-admin-reply', args=[message.pk]),
                {'body': 'Another reply'},
                format='json',
            ).status_code
            == 201
        )
        message.refresh_from_db()
        assert message.admin_reply == 'Here to help'
        assert message.replied_at is not None
        assert UserMessage.objects.filter(is_from_admin=True, user=message.user).count() == 1

    def test_change_only_staff_cannot_use_get_to_bypass_view_permission(
        self, client, staff, message
    ):
        client.force_authenticate(grant(staff, 'contact.change_usermessage'))
        assert client.get(reverse('contact-admin-detail', args=[message.pk])).status_code == 403
        message.refresh_from_db()
        assert message.is_read is False

    def test_non_staff_with_support_permissions_remains_customer_scoped(
        self, client, customer, message
    ):
        client.force_authenticate(
            grant(customer, 'contact.view_usermessage', 'contact.change_usermessage')
        )
        assert client.get(reverse('contact-admin-list')).status_code == 403
        assert client.get(reverse('contact-admin-detail', args=[message.pk])).status_code == 403
        assert (
            client.post(
                reverse('contact-admin-reply', args=[message.pk]), {'body': 'No'}, format='json'
            ).status_code
            == 403
        )
        assert client.get(reverse('contact-my-list')).data['count'] == 1
        message.refresh_from_db()
        assert message.is_read is False

    @pytest.mark.parametrize('role,expected', [('staff', 403), ('viewer', 200), ('customer', 403)])
    def test_couriers_are_listed_only_with_staff_courier_view_permission(
        self, client, staff, customer, role, expected
    ):
        Courier.objects.create(user=customer, phone='+998901234567')
        account = customer if role == 'customer' else staff
        if role in ('viewer', 'customer'):
            account = grant(account, 'marketplace.view_courier')
        client.force_authenticate(account)
        response = client.get(reverse('marketplace-courier-list'))
        assert response.status_code == expected
        if expected == 200:
            assert response.data['count'] == 1
