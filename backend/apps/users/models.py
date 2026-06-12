from django.contrib.auth.models import AbstractUser
from django.db import models
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

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')

    def __str__(self):
        return self.email
