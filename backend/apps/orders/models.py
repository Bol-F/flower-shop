from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.products.models import Product


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        CONFIRMED = 'confirmed', _('Confirmed')
        PROCESSING = 'processing', _('Processing')
        SHIPPED = 'shipped', _('Shipped')
        DELIVERED = 'delivered', _('Delivered')
        CANCELLED = 'cancelled', _('Cancelled')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name=_('user'),
    )
    status = models.CharField(_('status'), max_length=20, choices=Status.choices, default=Status.PENDING)
    total_price = models.DecimalField(_('total price'), max_digits=10, decimal_places=2)
    shipping_address = models.TextField(_('shipping address'))
    phone = models.CharField(_('phone'), max_length=20)
    notes = models.TextField(_('notes'), blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('Order')
        verbose_name_plural = _('Orders')
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} by {self.user.email}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='items', verbose_name=_('order'))
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL, null=True, verbose_name=_('product'))
    product_name = models.CharField(_('product name'), max_length=200)
    product_price = models.DecimalField(_('product price'), max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(_('quantity'))

    class Meta:
        verbose_name = _('Order item')
        verbose_name_plural = _('Order items')

    def __str__(self):
        return f"{self.quantity}x {self.product_name}"

    @property
    def subtotal(self):
        return self.product_price * self.quantity
