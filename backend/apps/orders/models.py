from django.conf import settings
from django.db import models
from django.utils import timezone
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
        ONLINE = 'online', _('Online payment')

    class PaymentStatus(models.TextChoices):
        UNPAID = 'unpaid', _('Unpaid')
        PENDING = 'pending', _('Pending')
        PAID = 'paid', _('Paid')
        FAILED = 'failed', _('Failed')
        REFUNDED = 'refunded', _('Refunded')

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
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH,
    )
    payment_status = models.CharField(
        _('payment status'),
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID,
    )
    payment_provider = models.CharField(
        _('payment provider'),
        max_length=60,
        blank=True,
        default='',
    )
    payment_reference = models.CharField(
        _('payment reference'),
        max_length=120,
        blank=True,
        default='',
    )
    paid_at = models.DateTimeField(_('paid at'), null=True, blank=True)
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
    delivery_zone = models.ForeignKey(
        'DeliveryZone',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name=_('delivery zone'),
    )
    delivery_requires_confirmation = models.BooleanField(
        _('delivery requires confirmation'),
        default=False,
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

    def save(self, *args, **kwargs):
        if self.payment_status == self.PaymentStatus.PAID and self.paid_at is None:
            self.paid_at = timezone.now()
            update_fields = kwargs.get('update_fields')
            if update_fields is not None:
                kwargs['update_fields'] = set(update_fields) | {'paid_at'}
        super().save(*args, **kwargs)


class DeliveryZone(models.Model):
    name = models.CharField(_('name'), max_length=120, unique=True)
    city = models.CharField(_('city'), max_length=80, default='Tashkent')
    fee = models.DecimalField(_('fee'), max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(_('is active'), default=True)
    requires_manual_confirmation = models.BooleanField(
        _('requires manual confirmation'),
        default=False,
    )
    description = models.TextField(_('description'), blank=True)
    polygon = models.JSONField(_('polygon'), blank=True, null=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('Delivery zone')
        verbose_name_plural = _('Delivery zones')
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def has_polygon(self):
        return bool(self.polygon)


class NotificationLog(models.Model):
    class Event(models.TextChoices):
        ORDER_CREATED = 'order_created', _('Order created')
        ORDER_CONFIRMED = 'order_confirmed', _('Order confirmed')
        ORDER_PREPARING = 'order_preparing', _('Order preparing')
        COURIER_PICKED_UP = 'courier_picked_up', _('Courier picked up')
        ORDER_DELIVERED = 'order_delivered', _('Order delivered')
        PAYMENT_STATUS_CHANGED = 'payment_status_changed', _('Payment status changed')

    class Channel(models.TextChoices):
        EMAIL = 'email', _('Email')
        TELEGRAM = 'telegram', _('Telegram')
        CONSOLE = 'console', _('Console')

    class Status(models.TextChoices):
        SUCCESS = 'success', _('Success')
        FAILED = 'failed', _('Failed')
        SKIPPED = 'skipped', _('Skipped')

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='notification_logs',
        verbose_name=_('order'),
    )
    event = models.CharField(_('event'), max_length=40, choices=Event.choices)
    channel = models.CharField(_('channel'), max_length=20, choices=Channel.choices)
    status = models.CharField(_('status'), max_length=20, choices=Status.choices)
    message = models.TextField(_('message'), blank=True)
    error = models.TextField(_('error'), blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('Notification log')
        verbose_name_plural = _('Notification logs')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_event_display()} via {self.get_channel_display()}'


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
