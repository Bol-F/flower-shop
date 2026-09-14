from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def populate_known_issuers(apps, schema_editor):
    SocialIdentity = apps.get_model('users', 'SocialIdentity')
    SocialIdentity.objects.filter(provider='google', issuer='').update(
        issuer='https://accounts.google.com'
    )
    SocialIdentity.objects.filter(provider='github', issuer='').update(
        issuer='https://github.com'
    )


def clear_known_issuers(apps, schema_editor):
    SocialIdentity = apps.get_model('users', 'SocialIdentity')
    SocialIdentity.objects.update(issuer='')


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0007_socialidentity_oauthloginattempt_oauthexchangecode_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='socialidentity',
            name='issuer',
            field=models.CharField(blank=True, default='', max_length=255),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name='OAuthLinkExchangeCode',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                (
                    'provider',
                    models.CharField(
                        choices=[
                            ('google', 'Google'),
                            ('github', 'GitHub'),
                            ('microsoft', 'Microsoft'),
                        ],
                        max_length=20,
                    ),
                ),
                ('issuer', models.CharField(blank=True, max_length=255)),
                ('subject', models.CharField(max_length=255)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('email_verified', models.BooleanField(default=False)),
                ('token_digest', models.CharField(max_length=64, unique=True)),
                ('expires_at', models.DateTimeField(db_index=True)),
                ('used_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                (
                    'linking_user',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='oauth_link_exchange_codes',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={'ordering': ('-created_at',)},
        ),
        migrations.RunPython(populate_known_issuers, clear_known_issuers),
        migrations.AlterField(
            model_name='oauthexchangecode',
            name='expires_at',
            field=models.DateTimeField(db_index=True),
        ),
        migrations.AlterField(
            model_name='oauthloginattempt',
            name='expires_at',
            field=models.DateTimeField(db_index=True),
        ),
        migrations.RemoveConstraint(
            model_name='socialidentity',
            name='unique_social_provider_subject',
        ),
        migrations.AddConstraint(
            model_name='socialidentity',
            constraint=models.UniqueConstraint(
                fields=('provider', 'issuer', 'subject'),
                name='unique_social_provider_issuer_subject',
            ),
        ),
    ]
