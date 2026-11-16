from datetime import timedelta
from importlib import import_module
from io import StringIO
from types import SimpleNamespace

import pytest
from django.contrib.auth.models import Group, Permission
from django.contrib.sessions.models import Session
from django.core.management import call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import Client, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken

from apps.contact.models import UserMessage
from apps.orders.models import Order
from apps.users.models import OAuthExchangeCode, OAuthLinkExchangeCode, OAuthLoginAttempt, User


def retire_accounts():
    migration = import_module('apps.users.migrations.0010_retire_public_demo_accounts')
    # Use historical models, as the migration runner does, rather than relying
    # on runtime User/Session methods that do not exist in a data migration.
    historical_apps = MigrationExecutor(connection).loader.project_state().apps
    migration.retire_public_demo_accounts(historical_apps, SimpleNamespace(connection=connection))


@pytest.mark.django_db
def test_retirement_revokes_demo_credentials_tokens_sessions_and_preserves_history(tmp_path):
    customer = User.objects.create_user('customer', 'customer@example.com', 'demo12345')
    staff = User.objects.create_user(
        'staff', 'STAFF@example.com', 'demo12345', is_staff=True, is_superuser=True
    )
    manager = User.objects.create_user(
        'private-manager', 'private-manager@example.test', 'private-password', is_staff=True
    )
    operations = Group.objects.create(name='Demo flower shop operations')
    permission = Permission.objects.get(content_type__app_label='orders', codename='view_order')
    operations.permissions.add(permission)
    for user in (customer, staff, manager):
        user.groups.add(operations)
        user.user_permissions.add(permission)

    manager_password = manager.password
    manager_token = RefreshToken.for_user(manager)
    demo_tokens = {user.pk: RefreshToken.for_user(user) for user in (customer, staff)}
    access_tokens = {user_id: str(token.access_token) for user_id, token in demo_tokens.items()}
    refresh_tokens = {user_id: str(token) for user_id, token in demo_tokens.items()}
    session_keys = {}
    for user in (customer, staff, manager):
        client = Client()
        client.force_login(user)
        session_keys[user.pk] = client.session.session_key
    malformed_key = 'malformed-demo-retirement-session'
    Session.objects.create(
        session_key=malformed_key,
        session_data='this-is-not-a-valid-session',
        expire_date=timezone.now() + timedelta(days=1),
    )

    saved_order = Order.objects.create(
        user=customer,
        total_price='10.00',
        shipping_address='Saved delivery address',
        phone='+998900000000',
        notes='Existing order history must survive retirement.',
    )
    saved_message = UserMessage.objects.create(
        user=customer, subject='Saved support history', body='Retain this conversation.'
    )
    expires_at = timezone.now() + timedelta(minutes=5)
    exchange = OAuthExchangeCode.objects.create(
        user=customer, token_digest='a' * 64, expires_at=expires_at
    )
    link_exchange = OAuthLinkExchangeCode.objects.create(
        linking_user=staff,
        provider='github',
        subject='retired-demo-subject',
        token_digest='b' * 64,
        expires_at=expires_at,
    )
    attempt = OAuthLoginAttempt.objects.create(
        linking_user=staff,
        provider='github',
        state_digest='c' * 64,
        code_verifier='test-only-verifier',
        nonce='test-only-nonce',
        expires_at=expires_at,
    )

    retire_accounts()
    # Migration re-entry and public cold starts cannot restore shared logins.
    retire_accounts()
    output = StringIO()
    with override_settings(MEDIA_ROOT=tmp_path):
        call_command('seed_demo', stdout=output)
        call_command('seed_demo', stdout=output)
    assert 'demo12345' not in output.getvalue()
    assert 'customer@example.com' not in output.getvalue()
    assert 'staff@example.com' not in output.getvalue()

    api = APIClient()
    for user in (customer, staff):
        user.refresh_from_db()
        assert not user.is_active
        assert not user.is_staff
        assert not user.is_superuser
        assert not user.has_usable_password()
        assert not user.groups.exists()
        assert not user.user_permissions.exists()
        assert not Session.objects.filter(session_key=session_keys[user.pk]).exists()
        assert (
            api.post(
                reverse('login'), {'email': user.email, 'password': 'demo12345'}, format='json'
            ).status_code
            == 401
        )
        assert (
            api.post(
                reverse('token-refresh'), {'refresh': refresh_tokens[user.pk]}, format='json'
            ).status_code
            == 401
        )
        api.credentials(HTTP_AUTHORIZATION=f'Bearer {access_tokens[user.pk]}')
        assert api.get(reverse('profile')).status_code == 401
        assert api.get('/api/orders/').status_code == 401
        api.credentials()
        assert BlacklistedToken.objects.filter(token__jti=demo_tokens[user.pk]['jti']).exists()

    for credential in (exchange, link_exchange, attempt):
        credential.refresh_from_db()
        assert credential.used_at is not None
        assert credential.expires_at <= timezone.now()
    assert attempt.code_verifier == ''
    assert attempt.nonce == ''
    saved_order.refresh_from_db()
    saved_message.refresh_from_db()
    assert saved_order.user_id == customer.pk
    assert saved_order.notes == 'Existing order history must survive retirement.'
    assert saved_message.user_id == customer.pk
    assert saved_message.body == 'Retain this conversation.'

    manager.refresh_from_db()
    assert manager.is_active and manager.is_staff
    assert manager.password == manager_password
    assert manager.check_password('private-password')
    assert manager.groups.filter(pk=operations.pk).exists()
    assert manager.user_permissions.filter(pk=permission.pk).exists()
    assert operations.permissions.filter(pk=permission.pk).exists()
    assert Session.objects.filter(session_key=session_keys[manager.pk]).exists()
    assert Session.objects.filter(session_key=malformed_key).exists()
    assert OutstandingToken.objects.filter(user=manager).exists()
    assert not BlacklistedToken.objects.filter(token__user=manager).exists()
    assert (
        api.post(
            reverse('token-refresh'), {'refresh': str(manager_token)}, format='json'
        ).status_code
        == 200
    )
    assert (
        api.post(
            reverse('login'),
            {'email': manager.email, 'password': 'private-password'},
            format='json',
        ).status_code
        == 200
    )


@pytest.mark.django_db
def test_retirement_does_not_match_unrelated_username_or_email_suffix():
    unrelated = User.objects.create_user(
        'staff', 'staff@example.com.example.test', 'private-password', is_staff=True
    )
    retire_accounts()
    unrelated.refresh_from_db()
    assert unrelated.is_active and unrelated.is_staff
    assert unrelated.check_password('private-password')
