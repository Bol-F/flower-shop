import re

from django.conf import settings
from django.db import migrations, models


MICROSOFT_CONSUMER_TENANT_ID = '9188040d-6c67-4c5b-b112-36a304b66dad'
MICROSOFT_TENANT_ID_RE = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    re.IGNORECASE,
)


def populate_unambiguous_microsoft_issuer(apps, schema_editor):
    """Upgrade legacy rows only when deployment scope identifies one tenant."""

    tenant = str(
        settings.OAUTH_PROVIDERS.get('microsoft', {}).get('tenant', '')
    ).strip().lower()
    if tenant == 'consumers':
        tenant = MICROSOFT_CONSUMER_TENANT_ID
    elif not MICROSOFT_TENANT_ID_RE.fullmatch(tenant):
        return

    SocialIdentity = apps.get_model('users', 'SocialIdentity')
    SocialIdentity.objects.filter(provider='microsoft', issuer='').update(
        issuer=f'https://login.microsoftonline.com/{tenant}/v2.0'
    )


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0008_oauth_issuer_and_link_exchange'),
    ]

    operations = [
        migrations.RunPython(
            populate_unambiguous_microsoft_issuer,
            migrations.RunPython.noop,
        ),
        migrations.AddConstraint(
            model_name='socialidentity',
            constraint=models.UniqueConstraint(
                fields=('user', 'provider'),
                name='unique_social_user_provider',
            ),
        ),
    ]
