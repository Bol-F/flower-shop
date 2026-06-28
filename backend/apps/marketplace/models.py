from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class City(models.Model):
    class Currency(models.TextChoices):
        UZS = 'UZS', _("Uzbek so'm")
        USD = 'USD', _('US Dollar')

    name = models.CharField(_('name'), max_length=100, unique=True)
    slug = models.SlugField(_('slug'), unique=True, blank=True)
    country = models.CharField(_('country'), max_length=100, default='Uzbekistan')
    currency = models.CharField(
        _('currency'),
        max_length=3,
        choices=Currency.choices,
        default=Currency.UZS,
    )
    is_active = models.BooleanField(_('is active'), default=True)
    default_delivery_fee = models.DecimalField(
        _('default delivery fee'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('2.37'),
        help_text=_('Stored in the backend base price unit.'),
    )
    free_delivery_threshold = models.DecimalField(
        _('free delivery threshold'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('39.53'),
        help_text=_('Stored in the backend base price unit.'),
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('City')
        verbose_name_plural = _('Cities')
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Vendor(models.Model):
    name = models.CharField(_('name'), max_length=160)
    slug = models.SlugField(_('slug'), unique=True, blank=True)
    phone = models.CharField(_('phone'), max_length=30, blank=True)
    address = models.TextField(_('address'), blank=True)
    city = models.ForeignKey(
        City,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vendors',
        verbose_name=_('city'),
    )
    is_active = models.BooleanField(_('is active'), default=True)
    commission_percent = models.DecimalField(
        _('commission percent'),
        max_digits=5,
        decimal_places=2,
        default=Decimal('10.00'),
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('Vendor')
        verbose_name_plural = _('Vendors')
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Courier(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = 'available', _('Available')
        BUSY = 'busy', _('Busy')
        OFFLINE = 'offline', _('Offline')

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='courier_profile',
        verbose_name=_('user'),
    )
    phone = models.CharField(_('phone'), max_length=30, blank=True)
    city = models.ForeignKey(
        City,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='couriers',
        verbose_name=_('city'),
    )
    is_active = models.BooleanField(_('is active'), default=True)
    current_status = models.CharField(
        _('current status'),
        max_length=20,
        choices=Status.choices,
        default=Status.OFFLINE,
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('Courier')
        verbose_name_plural = _('Couriers')
        ordering = ['user__email']

    def __str__(self):
        return f'{self.user.email} ({self.get_current_status_display()})'


class PromoCode(models.Model):
    class DiscountType(models.TextChoices):
        FIXED_AMOUNT = 'fixed_amount', _('Fixed amount')
        PERCENT = 'percent', _('Percent')

    code = models.CharField(_('code'), max_length=40, unique=True)
    discount_type = models.CharField(
        _('discount type'),
        max_length=20,
        choices=DiscountType.choices,
    )
    discount_value = models.DecimalField(_('discount value'), max_digits=10, decimal_places=2)
    min_order_amount = models.DecimalField(
        _('minimum order amount'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
    )
    max_discount_amount = models.DecimalField(
        _('maximum discount amount'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(_('is active'), default=True)
    valid_from = models.DateTimeField(_('valid from'), default=timezone.now)
    valid_until = models.DateTimeField(_('valid until'), null=True, blank=True)
    usage_limit = models.PositiveIntegerField(_('usage limit'), null=True, blank=True)
    used_count = models.PositiveIntegerField(_('used count'), default=0)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('Promo code')
        verbose_name_plural = _('Promo codes')
        ordering = ['code']

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        self.code = self.code.strip().upper()
        super().save(*args, **kwargs)


class WishlistItem(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wishlist_items',
        verbose_name=_('user'),
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='wishlisted_by',
        verbose_name=_('product'),
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('Wishlist item')
        verbose_name_plural = _('Wishlist items')
        unique_together = ('user', 'product')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.email} -> {self.product.name}'
