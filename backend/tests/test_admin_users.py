"""Admin-created users need an email login and safe staff role boundaries."""

import pytest
from apps.users.models import User
from django.contrib import admin
from django.contrib.auth.models import Permission
from django.test import RequestFactory
from django.urls import reverse


@pytest.fixture
def superuser(db):
    return User.objects.create_superuser(
        username='admin-owner', email='admin-owner@example.test', password='StrongPass123!'
    )


@pytest.fixture
def staff(db):
    user = User.objects.create_user(
        username='customer-manager',
        email='customer-manager@example.test',
        password='StrongPass123!',
        is_staff=True,
    )
    user.user_permissions.add(
        Permission.objects.get(content_type__app_label='users', codename='add_user'),
        Permission.objects.get(content_type__app_label='users', codename='change_user'),
        Permission.objects.get(content_type__app_label='users', codename='view_user'),
    )
    return user


@pytest.fixture
def customer(db):
    return User.objects.create_user(
        username='customer',
        email='customer@example.test',
        password='StrongPass123!',
        loyalty_points=25,
    )


def add_payload(email='new-customer@example.test'):
    return {
        'email': email,
        'username': 'new-customer',
        'password1': 'AnotherStrongPass123!',
        'password2': 'AnotherStrongPass123!',
        '_save': 'Save',
    }


@pytest.mark.django_db
class TestAdminUsers:
    def test_add_form_requires_email_login_identity(self, superuser, client):
        client.force_login(superuser)
        url = reverse('admin:users_user_add')

        response = client.get(url)
        missing_email = client.post(url, add_payload(email=''))

        assert response.status_code == 200
        assert 'email' in response.context['adminform'].form.fields
        assert response.context['adminform'].form.fields['email'].required
        assert missing_email.status_code == 200
        assert 'email' in missing_email.context['adminform'].form.errors
        assert not User.objects.filter(username='new-customer').exists()

    def test_admin_creation_normalizes_email_and_rejects_case_duplicate(self, superuser, client):
        client.force_login(superuser)
        url = reverse('admin:users_user_add')

        created = client.post(url, add_payload(email=' New-Customer@Example.TEST '))

        assert created.status_code == 302
        assert User.objects.get(username='new-customer').email == 'new-customer@example.test'

        duplicate = add_payload(email='NEW-CUSTOMER@example.test')
        duplicate['username'] = 'other-customer'
        rejected = client.post(url, duplicate)

        assert rejected.status_code == 200
        assert 'email' in rejected.context['adminform'].form.errors
        assert not User.objects.filter(username='other-customer').exists()

    def test_non_superuser_cannot_edit_role_fields_or_loyalty_balance(self, staff, customer):
        request = RequestFactory().get('/admin/users/user/')
        request.user = staff
        user_admin = admin.site._registry[User]

        readonly = set(user_admin.get_readonly_fields(request, customer))
        form_fields = set(user_admin.get_form(request, customer).base_fields)

        assert {
            'loyalty_points',
            'is_staff',
            'is_superuser',
            'groups',
            'user_permissions',
        } <= readonly
        assert not readonly.intersection(form_fields)
        assert user_admin.has_change_permission(request, customer)

    def test_forged_change_post_cannot_escalate_customer_or_grant_points(
        self, staff, customer, client
    ):
        client.force_login(staff)
        response = client.post(
            reverse('admin:users_user_change', args=[customer.pk]),
            {
                'username': customer.username,
                'email': customer.email,
                'first_name': '',
                'last_name': '',
                'is_active': 'on',
                'phone': '',
                'address': '',
                'city': customer.city,
                'language': customer.language,
                'currency': customer.currency,
                'loyalty_points': '999999',
                'is_staff': 'on',
                'is_superuser': 'on',
                '_save': 'Save',
            },
        )

        customer.refresh_from_db()
        assert response.status_code == 302, response.context['adminform'].form.errors
        assert customer.loyalty_points == 25
        assert customer.is_staff is False
        assert customer.is_superuser is False

    def test_non_superuser_cannot_access_or_change_staff_accounts(self, staff, superuser, client):
        request = RequestFactory().get('/admin/users/user/')
        request.user = staff
        user_admin = admin.site._registry[User]

        assert not user_admin.get_queryset(request).filter(pk=superuser.pk).exists()
        assert not user_admin.has_change_permission(request, superuser)
        assert not user_admin.has_delete_permission(request, superuser)

        client.force_login(staff)
        response = client.get(reverse('admin:users_user_change', args=[superuser.pk]))
        assert response.status_code == 302
        assert response.url == reverse('admin:index')
