"""Retire shared-password demo identities without deleting their history."""

from django.contrib.auth import SESSION_KEY
from django.contrib.auth.hashers import make_password
from django.contrib.sessions.backends.db import SessionStore
from django.db import migrations
from django.db.models import Q
from django.utils import timezone


def retire_public_demo_accounts(apps, schema_editor):
    database = schema_editor.connection.alias
    User = apps.get_model('users', 'User')
    demo_users = list(
        User.objects.using(database).filter(
            Q(email__iexact='customer@example.com') | Q(email__iexact='staff@example.com')
        )
    )
    if not demo_users:
        return

    user_ids = [user.pk for user in demo_users]
    for user in demo_users:
        user.is_active = False
        user.is_staff = False
        user.is_superuser = False
        user.password = make_password(None)
        user.save(
            using=database,
            update_fields=('is_active', 'is_staff', 'is_superuser', 'password'),
        )
        user.groups.clear()
        user.user_permissions.clear()

    OutstandingToken = apps.get_model('token_blacklist', 'OutstandingToken')
    BlacklistedToken = apps.get_model('token_blacklist', 'BlacklistedToken')
    for token_id in (
        OutstandingToken.objects.using(database)
        .filter(user_id__in=user_ids)
        .values_list('pk', flat=True)
    ):
        BlacklistedToken.objects.using(database).get_or_create(token_id=token_id)

    now = timezone.now()
    apps.get_model('users', 'OAuthExchangeCode').objects.using(database).filter(
        user_id__in=user_ids, used_at__isnull=True
    ).update(used_at=now, expires_at=now)
    apps.get_model('users', 'OAuthLinkExchangeCode').objects.using(database).filter(
        linking_user_id__in=user_ids, used_at__isnull=True
    ).update(used_at=now, expires_at=now)
    apps.get_model('users', 'OAuthLoginAttempt').objects.using(database).filter(
        linking_user_id__in=user_ids, used_at__isnull=True
    ).update(used_at=now, expires_at=now, code_verifier='', nonce='')

    # Historical migration models have no get_decoded() method. Use the same
    # decoder as the database session backend, and retain unrelated sessions.
    Session = apps.get_model('sessions', 'Session')
    decoder = SessionStore()
    retired_ids = {str(user_id) for user_id in user_ids}
    session_keys = []
    for session in Session.objects.using(database).filter(expire_date__gt=now).iterator():
        try:
            data = decoder.decode(session.session_data)
        except Exception:
            # A malformed session is already unusable; it is not proof of ownership.
            continue
        if isinstance(data, dict) and str(data.get(SESSION_KEY)) in retired_ids:
            session_keys.append(session.session_key)
    Session.objects.using(database).filter(session_key__in=session_keys).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0009_socialidentity_user_provider'),
        ('sessions', '0001_initial'),
        ('token_blacklist', '0013_alter_blacklistedtoken_options_and_more'),
    ]

    operations = [
        # Rolling back a release must never restore published passwords/access.
        migrations.RunPython(retire_public_demo_accounts, migrations.RunPython.noop),
    ]
