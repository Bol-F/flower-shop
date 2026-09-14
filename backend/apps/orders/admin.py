from django.contrib import admin, messages
from django.db.models import Count
from django.template.response import TemplateResponse
from django.urls import path
from django.utils import timezone
from django.utils.formats import date_format
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from apps.marketplace.services import award_loyalty_points_if_eligible

from . import notifications
from .models import DeliveryZone, NotificationLog, Order, OrderItem, PaymentAttempt, PaymentEvent
from .payments import update_payment_status


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'product_name', 'product_price', 'quantity', 'subtotal')
    can_delete = False

    @admin.display(description=_('Subtotal'))
    def subtotal(self, obj):
        return obj.subtotal

    def has_add_permission(self, request, obj=None):
        return False


class NotificationLogInline(admin.TabularInline):
    model = NotificationLog
    extra = 0
    readonly_fields = (
        'event_type',
        'channel',
        'recipient',
        'subject',
        'status',
        'message',
        'error_message',
        'created_at',
        'sent_at',
    )
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(DeliveryZone)
class DeliveryZoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'fee', 'is_active', 'requires_manual_confirmation')
    list_filter = ('city', 'is_active', 'requires_manual_confirmation')
    search_fields = ('name', 'city__name', 'description')
    search_help_text = _('Find delivery zones by name, city, or description.')
    list_per_page = 25
    list_editable = ('city', 'fee', 'is_active', 'requires_manual_confirmation')
    list_select_related = ('city',)


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'related_order',
        'event_type',
        'channel',
        'recipient',
        'status',
        'created_at',
        'sent_at',
    )
    list_filter = ('event_type', 'channel', 'status', 'created_at')
    list_select_related = ('related_order',)
    list_per_page = 25
    search_help_text = _('Find notifications by order number, recipient, or message.')
    search_fields = (
        'related_order__id',
        'recipient',
        'subject',
        'message',
        'error_message',
    )
    readonly_fields = (
        'related_order',
        'event_type',
        'channel',
        'recipient',
        'subject',
        'status',
        'message',
        'error_message',
        'created_at',
        'sent_at',
    )

    def has_add_permission(self, request):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    change_list_template = 'admin/orders/order/change_list.html'
    list_display = (
        'id',
        'recipient_name',
        'status',
        'payment_badge',
        'delivery_schedule',
        'assigned_courier',
        'total_price',
    )
    list_display_links = ('id', 'recipient_name')
    list_filter = (
        'city',
        'vendor',
        'assigned_courier',
        'status',
        'payment_method',
        'payment_status',
        'payment_provider',
        'delivery_zone',
        'delivery_requires_confirmation',
        'delivery_date',
        'delivery_time_slot',
        'created_at',
    )
    search_fields = (
        'id',
        'user__email',
        'user__username',
        'phone',
        'shipping_address',
        'delivery_address',
        'recipient_name',
        'recipient_phone',
        'delivery_zone__name',
        'city__name',
        'vendor__name',
    )
    search_help_text = _(
        'Find an order by number, customer, recipient, phone, address, or florist.'
    )
    list_editable = ('status', 'assigned_courier')
    list_select_related = ('user', 'city', 'vendor', 'assigned_courier', 'delivery_zone')
    date_hierarchy = 'created_at'
    list_per_page = 25
    readonly_fields = (
        'user',
        'delivery_fee',
        'discount_amount',
        'total_price',
        'loyalty_points_earned',
        'map_preview',
        'payment_status',
        'payment_provider',
        'payment_reference',
        'paid_at',
        'inventory_released_at',
        'created_at',
        'updated_at',
    )
    inlines = (OrderItemInline, NotificationLogInline)
    actions = (
        'mark_cash_paid',
        'mark_confirmed',
        'mark_preparing',
        'mark_courier_picked_up',
        'mark_delivered',
    )

    fieldsets = (
        (
            _('Order details'),
            {
                'fields': (
                    'user',
                    'city',
                    'vendor',
                    'status',
                ),
            },
        ),
        (
            _('Payment & totals'),
            {
                'fields': (
                    'payment_method',
                    'payment_status',
                    'payment_provider',
                    'payment_reference',
                    'paid_at',
                    'promo_code',
                    'discount_amount',
                    'delivery_fee',
                    'total_price',
                    'loyalty_points_earned',
                ),
            },
        ),
        (
            _('Delivery'),
            {
                'fields': (
                    'assigned_courier',
                    'courier_assigned_at',
                    'courier_picked_up_at',
                    'delivered_at',
                    'delivery_date',
                    'delivery_time_slot',
                    'delivery_address',
                    'delivery_zone',
                    'delivery_requires_confirmation',
                    ('delivery_lat', 'delivery_lng'),
                    'map_preview',
                    'shipping_address',
                    'phone',
                    'notes',
                ),
            },
        ),
        (
            _('Recipient'),
            {
                'fields': (
                    'recipient_name',
                    'recipient_phone',
                    'gift_note',
                    'call_recipient_before_delivery',
                ),
            },
        ),
        (_('Timestamps'), {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related('city', 'vendor', 'assigned_courier', 'delivery_zone')
            .annotate(_item_count=Count('items'))
        )

    def has_delete_permission(self, request, obj=None):
        """Keep order and payment audit history intact."""
        return False

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'delivery-map/',
                self.admin_site.admin_view(self.delivery_map_view),
                name='orders_order_delivery_map',
            ),
        ]
        return custom_urls + urls

    def delivery_map_view(self, request):
        orders = (
            Order.objects.select_related('user')
            .exclude(delivery_lat__isnull=True)
            .exclude(delivery_lng__isnull=True)
            .order_by('-created_at')[:200]
        )
        orders_data = [
            {
                'id': order.id,
                'customer': order.user.email,
                'status': order.get_status_display(),
                'address': order.delivery_address or order.shipping_address,
                'lat': float(order.delivery_lat),
                'lng': float(order.delivery_lng),
            }
            for order in orders
        ]
        context = {
            **self.admin_site.each_context(request),
            'title': _('Delivery map'),
            'orders_data': orders_data,
            'opts': self.model._meta,
        }
        return TemplateResponse(request, 'admin/orders/order/delivery_map.html', context)

    @admin.display(description=_('Map'))
    def map_preview(self, obj):
        if obj.delivery_lat is None or obj.delivery_lng is None:
            return _('No map point selected')

        lat = float(obj.delivery_lat)
        lng = float(obj.delivery_lng)
        bbox = f'{lng - 0.01},{lat - 0.01},{lng + 0.01},{lat + 0.01}'
        embed_url = (
            'https://www.openstreetmap.org/export/embed.html'
            f'?bbox={bbox}&layer=mapnik&marker={lat},{lng}'
        )
        open_url = f'https://www.openstreetmap.org/?mlat={lat}&mlon={lng}#map=16/{lat}/{lng}'
        return format_html(
            '<p><a href="{}" target="_blank" rel="noopener">Open in OpenStreetMap</a></p>'
            '<iframe src="{}" width="100%" height="240" '
            'style="border:1px solid #ddd;border-radius:8px"></iframe>',
            open_url,
            embed_url,
        )

    @admin.display(description=_('Items'))
    def item_count(self, obj):
        return obj._item_count

    @admin.display(description=_('Delivery'), ordering='delivery_date')
    def delivery_schedule(self, obj):
        return format_html(
            '<span class="flower-delivery-date">{}</span><small class="flower-delivery-slot">{}</small>',
            date_format(obj.delivery_date, 'j M Y') if obj.delivery_date else '—',
            obj.get_delivery_time_slot_display(),
        )

    @admin.display(description=_('Payment'), ordering='payment_status')
    def payment_badge(self, obj):
        tones = {
            Order.PaymentStatus.PAID: 'success',
            Order.PaymentStatus.FAILED: 'danger',
            Order.PaymentStatus.PENDING: 'warning',
            Order.PaymentStatus.UNPAID: 'warning',
            Order.PaymentStatus.REFUNDED: 'neutral',
        }
        return format_html(
            '<span class="flower-badge flower-badge--{}">{} · {}</span>',
            tones.get(obj.payment_status, 'neutral'),
            obj.get_payment_method_display(),
            obj.get_payment_status_display(),
        )

    @admin.action(description=_('Mark selected cash orders as paid'))
    def mark_cash_paid(self, request, queryset):
        eligible_orders = queryset.filter(
            payment_method=Order.PaymentMethod.CASH,
        ).exclude(payment_status=Order.PaymentStatus.PAID)
        eligible_ids = set(eligible_orders.values_list('id', flat=True))
        skipped = queryset.count() - len(eligible_ids)

        updated = 0
        for order in eligible_orders:
            update_payment_status(
                order,
                Order.PaymentStatus.PAID,
                payment_provider='cash',
                actor=request.user,
                reason=_('Cash payment recorded in Django administration.'),
            )
            updated += 1

        if updated:
            self.message_user(
                request,
                _('%(count)d cash order was marked paid.') % {'count': updated},
                level=messages.SUCCESS,
            )
        if skipped:
            self.message_user(
                request,
                _('%(count)d order was skipped because it was not unpaid cash.')
                % {'count': skipped},
                level=messages.WARNING,
            )

    @admin.action(description=_('Mark selected orders as confirmed'))
    def mark_confirmed(self, request, queryset):
        self._mark_status(queryset, Order.Status.CONFIRMED)

    @admin.action(description=_('Mark selected orders as preparing'))
    def mark_preparing(self, request, queryset):
        self._mark_status(queryset, Order.Status.PREPARING)

    @admin.action(description=_('Mark selected orders as courier picked up'))
    def mark_courier_picked_up(self, request, queryset):
        self._mark_status(queryset, Order.Status.COURIER_PICKED_UP)

    @admin.action(description=_('Mark selected orders as delivered'))
    def mark_delivered(self, request, queryset):
        self._mark_status(queryset, Order.Status.DELIVERED)

    def _mark_status(self, queryset, status):
        for order in queryset:
            order.status = status
            update_fields = ['status', 'updated_at']
            if status == Order.Status.COURIER_PICKED_UP and order.courier_picked_up_at is None:
                order.courier_picked_up_at = timezone.now()
                update_fields.append('courier_picked_up_at')
            if status == Order.Status.DELIVERED and order.delivered_at is None:
                order.delivered_at = timezone.now()
                update_fields.append('delivered_at')
            order.save(update_fields=update_fields)
            award_loyalty_points_if_eligible(order)
            notifications.notify_order_status_changed(order)


@admin.register(PaymentAttempt)
class PaymentAttemptAdmin(admin.ModelAdmin):
    list_display = ('public_id', 'order', 'provider', 'amount', 'currency', 'status', 'created_at')
    list_filter = ('provider', 'status', 'currency', 'created_at')
    search_fields = ('public_id', 'external_payment_id', 'provider_reference', 'order__id')
    search_help_text = _('Find a payment by reference or order number.')
    list_select_related = ('order',)
    list_per_page = 25
    readonly_fields = tuple(field.name for field in PaymentAttempt._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PaymentEvent)
class PaymentEventAdmin(admin.ModelAdmin):
    list_display = ('payment', 'source', 'event_type', 'status_from', 'status_to', 'created_at')
    list_filter = ('source', 'event_type', 'status_to', 'created_at')
    search_fields = ('payment__public_id', 'external_event_id', 'message')
    search_help_text = _('Find an event by payment reference, event ID, or message.')
    list_select_related = ('payment',)
    list_per_page = 25
    readonly_fields = tuple(field.name for field in PaymentEvent._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
