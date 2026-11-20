from django.contrib.auth.models import AbstractUser
from django.db import models, router, transaction
from django.db.models.functions import Lower
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    class Language(models.TextChoices):
        EN = 'EN', _('English')
        RU = 'RU', _('Russian')
        UZ = 'UZ', _('Uzbek')

    class Currency(models.TextChoices):
        USD = 'USD', _('US Dollar')
        UZS = 'UZS', _("Uzbek so'm")

    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        help_text=_('Required. 150 characters or fewer.'),
        error_messages={
            'unique': _('A user with that username already exists.'),
        },
    )
    email = models.EmailField(_('email address'), unique=True)
    phone = models.CharField(_('phone'), max_length=20, blank=True)
    address = models.TextField(_('address'), blank=True)
    bio = models.TextField(_('bio'), blank=True)
    city = models.CharField(_('city'), max_length=80, default='Tashkent')
    language = models.CharField(
        _('language'),
        max_length=2,
        choices=Language.choices,
        default=Language.EN,
    )
    currency = models.CharField(
        _('currency'),
        max_length=3,
        choices=Currency.choices,
        default=Currency.USD,
    )
    loyalty_points = models.PositiveIntegerField(_('loyalty points'), default=0)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        constraints = [
            models.UniqueConstraint(Lower('email'), name='users_email_ci_unique'),
        ]

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        update_fields = kwargs.get('update_fields')
        if self._state.adding or (update_fields is not None and 'password' not in update_fields):
            return super().save(*args, **kwargs)
        database = kwargs.get('using') or router.db_for_write(type(self), instance=self)
        with transaction.atomic(using=database):
            previous_password = (
                type(self)
                .objects.using(database)
                .select_for_update()
                .filter(pk=self.pk)
                .values_list('password', flat=True)
                .first()
            )
            result = super().save(*args, **kwargs)
            if previous_password is not None and previous_password != self.password:
                self._revoke_password_credentials(database)
            return result

    def _revoke_password_credentials(self, database):
        # Django admin and API password changes must have the same effect.
        # Keep account -> credential lock order consistent with OAuth and JWT
        # exchange. No providers or external services are contacted here.
        from rest_framework_simplejwt.token_blacklist.models import (
            BlacklistedToken,
            OutstandingToken,
        )

        now = timezone.now()
        outstanding = OutstandingToken.objects.using(database).filter(
            user=self,
            expires_at__gt=now,
            blacklistedtoken__isnull=True,
        )
        BlacklistedToken.objects.using(database).bulk_create(
            [
                BlacklistedToken(token_id=token_id)
                for token_id in outstanding.values_list('pk', flat=True)
            ],
            ignore_conflicts=True,
            batch_size=1000,
        )
        OAuthExchangeCode.objects.using(database).filter(user=self, expires_at__gt=now).update(
            expires_at=now,
        )
        OAuthLinkExchangeCode.objects.using(database).filter(
            linking_user=self,
            expires_at__gt=now,
        ).update(expires_at=now)
        # Include callbacks that consumed their state before the provider HTTP
        # request started, so they cannot create a fresh linking credential.
        OAuthLoginAttempt.objects.using(database).filter(
            linking_user=self,
            expires_at__gt=now,
        ).update(expires_at=now)


class SocialIdentity(models.Model):
    class Provider(models.TextChoices):
        GOOGLE = 'google', 'Google'
        GITHUB = 'github', 'GitHub'
        MICROSOFT = 'microsoft', 'Microsoft'

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='social_identities',
    )
    provider = models.CharField(max_length=20, choices=Provider.choices)
    # OIDC subjects are unique within an issuer, not globally.  Keeping the
    # canonical issuer also makes Microsoft multi-tenant identities safe.
    issuer = models.CharField(max_length=255, blank=True)
    subject = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('provider', 'issuer', 'subject'),
                name='unique_social_provider_issuer_subject',
            ),
            models.UniqueConstraint(
                fields=('user', 'provider'),
                name='unique_social_user_provider',
            ),
        ]
        ordering = ('provider',)

    def __str__(self):
        return f'{self.provider}:{self.issuer}:{self.subject}'


class OAuthLoginAttempt(models.Model):
    provider = models.CharField(max_length=20, choices=SocialIdentity.Provider.choices)
    state_digest = models.CharField(max_length=64, unique=True)
    code_verifier = models.CharField(max_length=128)
    nonce = models.CharField(max_length=128)
    next_path = models.CharField(max_length=500, default='/profile')
    linking_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='oauth_link_attempts',
    )
    expires_at = models.DateTimeField(db_index=True)
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)


class OAuthExchangeCode(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='oauth_exchange_codes',
    )
    token_digest = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField(db_index=True)
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)


class OAuthLinkExchangeCode(models.Model):
    """Short-lived provider identity awaiting confirmation by the JWT user."""

    linking_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='oauth_link_exchange_codes',
    )
    provider = models.CharField(max_length=20, choices=SocialIdentity.Provider.choices)
    issuer = models.CharField(max_length=255, blank=True)
    subject = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    email_verified = models.BooleanField(default=False)
    token_digest = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField(db_index=True)
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)
