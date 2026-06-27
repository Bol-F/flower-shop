from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.products.models import Product


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        CONFIRMED = 'confirmed', _('Confirmed')
        PREPARING = 'preparing', _('Preparing')
        COURIER_PICKED_UP = 'courier_picked_up', _('Courier picked up')
        PROCESSING = 'processing', _('Processing')
        SHIPPED = 'shipped', _('Shipped')
        DELIVERED = 'delivered', _('Delivered')
        CANCELLED = 'cancelled', _('Cancelled')

    class PaymentMethod(models.TextChoices):
        CASH = 'cash', _('Cash')
        CARD = 'card', _('Card')

    class DeliveryTimeSlot(models.TextChoices):
        MORNING = '09:00-12:00', _('09:00-12:00')
        MIDDAY = '12:00-15:00', _('12:00-15:00')
        AFTERNOON = '15:00-18:00', _('15:00-18:00')
        EVENING = '18:00-21:00', _('18:00-21:00')

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
    payment_method = models.CharField(
        _('payment method'),
        max_length=10,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH,
    )
    delivery_address = models.TextField(_('delivery address'), blank=True)
    delivery_lat = models.DecimalField(
        _('delivery latitude'),
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )
    delivery_lng = models.DecimalField(
        _('delivery longitude'),
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )
    delivery_date = models.DateField(_('delivery date'), null=True, blank=True)
    delivery_time_slot = models.CharField(
        _('delivery time slot'),
        max_length=20,
        choices=DeliveryTimeSlot.choices,
        blank=True,
    )
    recipient_name = models.CharField(_('recipient name'), max_length=150, blank=True)
    recipient_phone = models.CharField(_('recipient phone'), max_length=20, blank=True)
    gift_note = models.TextField(_('gift note'), blank=True)
    call_recipient_before_delivery = models.BooleanField(
        _('call recipient before delivery'),
        default=False,
    )
    delivery_fee = models.DecimalField(
        _('delivery fee'),
        max_digits=10,
        decimal_places=2,
        default=0,
    )
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
