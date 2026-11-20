import hashlib
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from types import SimpleNamespace
from importlib import import_module
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import pytest
from django.db import IntegrityError, close_old_connections, connection, models, transaction
from django.contrib import admin
from django.contrib.auth.models import Group
from django.test import RequestFactory, override_settings
from django.test.utils import isolate_apps
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import OAuthExchangeCode, OAuthLinkExchangeCode, OAuthLoginAttempt, User
from .admin import UserAdmin
from .oauth import ProviderIdentity
from .serializers import ChangePasswordSerializer, RegisterSerializer, UserProfileSerializer


OLD_PASSWORD = 'StrongOriginalPass123!'
NEW_PASSWORD = 'FreshDifferentPass456!'


@pytest.fixture
def security_user(db):
    return User.objects.create_user('security-user', 'security@example.test', OLD_PASSWORD)


def password_change(client):
    return client.post(
        reverse('profile-password'),
        {
            'old_password': OLD_PASSWORD,
            'new_password': NEW_PASSWORD,
            'new_password_confirm': NEW_PASSWORD,
        },
        format='json',
    )


@pytest.mark.django_db
@pytest.mark.parametrize('credential', ('access', 'refresh'))
def test_password_change_revokes_previously_issued_jwt(security_user, credential):
    client = APIClient()
    login = client.post(
        reverse('login'),
        {'email': security_user.email, 'password': OLD_PASSWORD},
        format='json',
    )
    assert login.status_code == 200
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {login.data["access"]}')
    assert password_change(client).status_code == 204
    if credential == 'access':
        response = client.get(reverse('profile'))
    else:
        client.credentials()
        response = client.post(
            reverse('token-refresh'), {'refresh': login.data['refresh']}, format='json'
        )
    assert response.status_code == 401
    client.credentials()
    fresh_login = client.post(
        reverse('login'),
        {'email': security_user.email, 'password': NEW_PASSWORD},
        format='json',
    )
    assert fresh_login.status_code == 200
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {fresh_login.data["access"]}')
    assert client.get(reverse('profile')).status_code == 200


@pytest.mark.django_db
def test_password_change_invalidates_pending_oauth_credentials(security_user):
    raw_code = 'pending-oauth-code'
    expiry = timezone.now() + timedelta(minutes=5)
    exchange = OAuthExchangeCode.objects.create(
        user=security_user,
        token_digest=hashlib.sha256(raw_code.encode()).hexdigest(),
        expires_at=expiry,
    )
    link = OAuthLinkExchangeCode.objects.create(
        linking_user=security_user,
        provider='github',
        subject='pending-subject',
        token_digest='link-digest',
        expires_at=expiry,
    )
    attempt = OAuthLoginAttempt.objects.create(
        linking_user=security_user,
        provider='github',
        state_digest='pending-state',
        code_verifier='pending-verifier',
        nonce='pending-nonce',
        expires_at=expiry,
        # Include an already consumed callback awaiting the provider response.
        used_at=timezone.now(),
    )
    client = APIClient()
    client.force_authenticate(security_user)
    assert password_change(client).status_code == 204
    client.force_authenticate(None)
    response = client.post(reverse('oauth-exchange'), {'code': raw_code}, format='json')
    assert response.status_code == 400
    for pending in (exchange, link, attempt):
        pending.refresh_from_db()
        assert pending.expires_at <= timezone.now()


@pytest.mark.django_db
def test_password_change_rechecks_password_at_save(security_user):
    payload = {
        'old_password': OLD_PASSWORD,
        'new_password': NEW_PASSWORD,
        'new_password_confirm': NEW_PASSWORD,
    }
    stale = ChangePasswordSerializer(
        data=payload, context={'request': SimpleNamespace(user=security_user)}
    )
    assert stale.is_valid(), stale.errors
    changed = User.objects.get(pk=security_user.pk)
    changed.set_password('InterveningPassword789!')
    changed.save(update_fields=['password'])
    with pytest.raises(ValidationError):
        stale.save()
    changed.refresh_from_db()
    assert changed.check_password('InterveningPassword789!')


@pytest.mark.django_db
def test_database_rejects_case_variant_email(security_user):
    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.create_user('other-username', security_user.email.upper(), OLD_PASSWORD)


@pytest.mark.django_db
def test_login_accepts_case_variants_of_existing_email(security_user):
    security_user.email = 'Mixed.Case@Example.test'
    security_user.save(update_fields=['email'])
    response = APIClient().post(
        reverse('login'),
        {
            'email': '  MIXED.CASE@example.TEST  ',
            'password': OLD_PASSWORD,
        },
        format='json',
    )
    assert response.status_code == 200
    security_user.refresh_from_db()
    assert security_user.email == 'Mixed.Case@Example.test'


@pytest.mark.django_db(transaction=True)
@isolate_apps()
def test_email_migration_refuses_duplicate_identities_without_modifying_accounts():
    migration = import_module('apps.users.migrations.0011_case_insensitive_email')

    class LegacyUser(models.Model):
        email = models.EmailField(unique=True)

        class Meta:
            app_label = 'users'
            db_table = 'test_legacy_email_identity_guard'

    # A separate table models the old case-sensitive schema without changing
    # the current users table or migrating other apps backwards.
    with connection.schema_editor() as editor:
        editor.create_model(LegacyUser)
    schema_editor = SimpleNamespace(connection=SimpleNamespace(alias='default'))
    apps = SimpleNamespace(get_model=lambda app_label, model_name: LegacyUser)
    try:
        emails = ['same@example.test', 'SAME@example.test']
        LegacyUser.objects.bulk_create([LegacyUser(email=email) for email in emails])
        with pytest.raises(RuntimeError, match='No accounts have been changed'):
            migration.reject_ambiguous_email_identities(apps, schema_editor)
        assert list(LegacyUser.objects.order_by('pk').values_list('email', flat=True)) == emails
    finally:
        with connection.schema_editor() as editor:
            editor.delete_model(LegacyUser)


@pytest.mark.django_db
def test_registration_race_returns_validation_error():
    serializers = []
    for username in ('first-registrant', 'second-registrant'):
        serializer = RegisterSerializer(
            data={
                'username': username,
                'email': 'race@example.test',
                'password': OLD_PASSWORD,
                'password_confirm': OLD_PASSWORD,
            }
        )
        assert serializer.is_valid(), serializer.errors
        serializers.append(serializer)
    serializers[0].save()
    with pytest.raises(ValidationError):
        serializers[1].save()


@pytest.mark.django_db
@pytest.mark.parametrize('credential', ('access', 'refresh'))
def test_admin_password_change_revokes_existing_jwt(security_user, credential):
    refresh = RefreshToken.for_user(security_user)
    access = str(refresh.access_token)
    security_user.set_password(NEW_PASSWORD)
    security_user.save(update_fields=['password'])
    client = APIClient()
    if credential == 'access':
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        response = client.get(reverse('profile'))
    else:
        response = client.post(reverse('token-refresh'), {'refresh': str(refresh)}, format='json')
    assert response.status_code == 401


@pytest.mark.django_db
def test_admin_password_change_revokes_pending_oauth_login_code(security_user):
    raw_code = 'pending-before-admin-reset'
    OAuthExchangeCode.objects.create(
        user=security_user,
        token_digest=hashlib.sha256(raw_code.encode()).hexdigest(),
        expires_at=timezone.now() + timedelta(minutes=5),
    )
    security_user.set_password(NEW_PASSWORD)
    security_user.save(update_fields=['password'])
    response = APIClient().post(reverse('oauth-exchange'), {'code': raw_code}, format='json')
    assert response.status_code == 400


@pytest.mark.django_db
def test_saving_other_fields_does_not_revoke_password_credentials(security_user):
    raw_code = 'still-valid-after-profile-save'
    OAuthExchangeCode.objects.create(
        user=security_user,
        token_digest=hashlib.sha256(raw_code.encode()).hexdigest(),
        expires_at=timezone.now() + timedelta(minutes=5),
    )
    security_user.set_password('ThisPasswordMustNotBeSaved789!')
    security_user.bio = 'Only update this field.'
    security_user.save(update_fields=['bio'])
    persisted = User.objects.get(pk=security_user.pk)
    assert persisted.check_password(OLD_PASSWORD)
    response = APIClient().post(reverse('oauth-exchange'), {'code': raw_code}, format='json')
    assert response.status_code == 200


@pytest.mark.django_db
def test_profile_edit_cannot_restore_stale_password(security_user):
    profile = UserProfileSerializer(
        security_user, data={'bio': 'New profile description'}, partial=True
    )
    assert profile.is_valid(), profile.errors
    current = User.objects.get(pk=security_user.pk)
    current.set_password(NEW_PASSWORD)
    current.save(update_fields=['password'])
    profile.save()
    current.refresh_from_db()
    assert current.check_password(NEW_PASSWORD)
    assert current.bio == 'New profile description'


@pytest.mark.django_db
def test_admin_profile_edit_preserves_concurrent_password_and_permission_changes(security_user):
    operator = User.objects.create_superuser('operator', 'operator@example.test', OLD_PASSWORD)
    request = RequestFactory().post('/admin/users/user/')
    request.user = operator
    model_admin = UserAdmin(User, admin.site)
    form_class = model_admin.get_form(request, security_user)
    form = form_class(
        data={
            'username': security_user.username,
            'email': security_user.email,
            'first_name': 'Edited name',
            'last_name': '',
            'is_active': 'on',
            'city': 'Tashkent',
            'language': 'EN',
            'currency': 'USD',
            'loyalty_points': '0',
        },
        instance=security_user,
    )
    assert form.is_valid(), form.errors
    stale = form.save(commit=False)
    current = User.objects.get(pk=security_user.pk)
    current.set_password(NEW_PASSWORD)
    current.is_staff = True
    current.save(update_fields=['password', 'is_staff'])
    group = Group.objects.create(name='New operations access')
    current.groups.add(group)
    model_admin.save_model(request, stale, form, change=True)
    model_admin.save_related(request, form, [], change=True)
    current.refresh_from_db()
    assert current.first_name == 'Edited name'
    assert current.check_password(NEW_PASSWORD)
    assert current.is_staff
    assert list(current.groups.values_list('pk', flat=True)) == [group.pk]


@pytest.mark.django_db
def test_refresh_for_deleted_user_returns_unauthorized(security_user):
    refresh = str(RefreshToken.for_user(security_user))
    security_user.delete()
    response = APIClient().post(reverse('token-refresh'), {'refresh': refresh}, format='json')
    assert response.status_code == 401


@pytest.mark.django_db
def test_password_change_preserves_whitespace_in_password(security_user):
    security_user.set_password(f'  {OLD_PASSWORD}  ')
    security_user.save(update_fields=['password'])
    client = APIClient()
    client.force_authenticate(security_user)
    password = f'  {NEW_PASSWORD}  '
    response = client.post(
        reverse('profile-password'),
        {
            'old_password': f'  {OLD_PASSWORD}  ',
            'new_password': password,
            'new_password_confirm': password,
        },
        format='json',
    )
    assert response.status_code == 204
    security_user.refresh_from_db()
    assert security_user.check_password(password)
    assert not security_user.check_password(password.strip())
    client.force_authenticate(None)
    assert (
        client.post(
            reverse('login'),
            {
                'email': security_user.email,
                'password': password,
            },
            format='json',
        ).status_code
        == 200
    )


@pytest.mark.django_db
def test_new_password_is_validated_against_account_details(security_user):
    client = APIClient()
    client.force_authenticate(security_user)
    response = client.post(
        reverse('profile-password'),
        {
            'old_password': OLD_PASSWORD,
            'new_password': 'security-user',
            'new_password_confirm': 'security-user',
        },
        format='json',
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_account_fields_cannot_be_elevated_via_profile(security_user):
    client = APIClient()
    client.force_authenticate(security_user)
    response = client.patch(
        reverse('profile'),
        {
            'is_staff': True,
            'is_superuser': True,
            'loyalty_points': 1000000,
            'user_permissions': [1],
            'email': 'takeover@example.test',
        },
        format='json',
    )
    assert response.status_code == 200
    assert response['Cache-Control'] == 'no-store'
    security_user.refresh_from_db()
    assert not security_user.is_staff and not security_user.is_superuser
    assert not security_user.user_permissions.exists()
    assert security_user.loyalty_points == 0
    assert security_user.email == 'security@example.test'


@pytest.mark.django_db
def test_password_change_during_oauth_link_callback_cancels_link(security_user):
    config = {
        'github': {
            'client_id': 'test-client',
            'client_secret': 'test-secret',
            'redirect_uri': 'http://testserver/api/auth/oauth/github/callback/',
        }
    }
    client = APIClient()
    client.force_authenticate(security_user)
    change_client = APIClient()
    change_client.force_authenticate(security_user)

    def change_password_before_provider_responds(*args):
        assert password_change(change_client).status_code == 204
        return ProviderIdentity(
            subject='unlinked-provider-user',
            issuer='https://github.com',
            email='new-provider@example.test',
            email_verified=True,
        )

    with override_settings(OAUTH_PROVIDERS=config):
        start = client.post(reverse('oauth-link-start', args=['github']))
        assert start.status_code == 200
        state = parse_qs(urlparse(start.data['authorization_url']).query)['state'][0]
        client.force_authenticate(None)
        with patch(
            'apps.users.views.exchange_provider_code',
            side_effect=change_password_before_provider_responds,
        ):
            response = client.get(
                reverse('oauth-callback', args=['github']),
                {'state': state, 'code': 'provider-code'},
            )
    assert response.status_code == 302
    assert 'link_code' not in parse_qs(urlparse(response['Location']).fragment)
    assert not OAuthLinkExchangeCode.objects.filter(linking_user=security_user).exists()


@pytest.mark.django_db(transaction=True)
def test_concurrent_refresh_rotates_credential_only_once():
    if connection.vendor != 'postgresql':
        pytest.skip('Concurrent row locks require PostgreSQL.')
    user = User.objects.create_user('refresh-race', 'refresh-race@example.test', OLD_PASSWORD)
    refresh = str(RefreshToken.for_user(user))
    barrier = Barrier(2)

    def rotate():
        close_old_connections()
        try:
            client = APIClient()
            barrier.wait(timeout=10)
            return client.post(
                reverse('token-refresh'), {'refresh': refresh}, format='json'
            ).status_code
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as executor:
        statuses = list(executor.map(lambda _: rotate(), range(2)))
    assert sorted(statuses) == [200, 401]
