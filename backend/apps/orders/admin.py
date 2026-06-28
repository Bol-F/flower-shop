from django.contrib import admin
from django.db.models import Count
from django.template.response import TemplateResponse
from django.urls import path
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from . import notifications
from .models import DeliveryZone, NotificationLog, Order, OrderItem
from .payments import update_payment_status
from apps.marketplace.services import award_loyalty_points_if_eligible


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
        'event', 'channel', 'status', 'message', 'error', 'created_at',
    )
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(DeliveryZone)
class DeliveryZoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'fee', 'is_active', 'requires_manual_confirmation')
    list_filter = ('city', 'is_active', 'requires_manual_confirmation')
    search_fields = ('name', 'city__name', 'description')
    list_editable = ('city', 'fee', 'is_active', 'requires_manual_confirmation')
    list_select_related = ('city',)


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'event', 'channel', 'status', 'created_at')
    list_filter = ('event', 'channel', 'status', 'created_at')
    search_fields = ('order__id', 'message', 'error')
    readonly_fields = (
        'order', 'event', 'channel', 'status', 'message', 'error', 'created_at',
    )

    def has_add_permission(self, request):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    change_list_template = 'admin/orders/order/change_list.html'
    list_display = (
        'id', 'user', 'city', 'vendor', 'status', 'payment_method', 'payment_status',
        'payment_provider', 'paid_at',
        'recipient_name', 'delivery_date', 'delivery_time_slot', 'delivery_zone',
        'assigned_courier',
        'delivery_fee', 'delivery_requires_confirmation',
        'total_price', 'item_count', 'created_at',
    )
    list_filter = (
        'city', 'vendor', 'assigned_courier', 'status',
        'payment_method', 'payment_status', 'payment_provider', 'delivery_zone',
        'delivery_requires_confirmation', 'delivery_date', 'delivery_time_slot',
        'created_at',
    )
    search_fields = (
        'id', 'user__email', 'user__username', 'phone', 'shipping_address',
        'delivery_address', 'recipient_name', 'recipient_phone',
        'delivery_zone__name', 'city__name', 'vendor__name',
    )
    list_editable = ('status', 'assigned_courier')
    list_select_related = ('user', 'city', 'vendor', 'assigned_courier', 'delivery_zone')
    date_hierarchy = 'created_at'
    list_per_page = 25
    readonly_fields = (
        'user', 'delivery_fee', 'discount_amount', 'total_price',
        'loyalty_points_earned', 'map_preview',
        'created_at', 'updated_at',
    )
    inlines = [OrderItemInline, NotificationLogInline]
    actions = (
        'mark_confirmed',
        'mark_preparing',
        'mark_courier_picked_up',
        'mark_delivered',
        'mark_payment_paid',
        'mark_payment_failed',
    )

    fieldsets = (
        (None, {
            'fields': (
                'user', 'city', 'vendor', 'status', 'payment_method', 'payment_status',
                'payment_provider', 'payment_reference', 'paid_at',
                'promo_code', 'discount_amount', 'delivery_fee', 'total_price',
                'loyalty_points_earned',
            ),
        }),
        (_('Delivery'), {
            'fields': (
                'assigned_courier', 'courier_assigned_at',
                'courier_picked_up_at', 'delivered_at',
                'delivery_date', 'delivery_time_slot', 'delivery_address',
                'delivery_zone', 'delivery_requires_confirmation',
                ('delivery_lat', 'delivery_lng'), 'map_preview',
                'shipping_address', 'phone', 'notes',
            ),
        }),
        (_('Recipient'), {
            'fields': (
                'recipient_name', 'recipient_phone', 'gift_note',
                'call_recipient_before_delivery',
            ),
        }),
        (_('Timestamps'), {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related('city', 'vendor', 'assigned_courier', 'delivery_zone')
            .annotate(_item_count=Count('items'))
        )

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

    @admin.action(description=_('Mark selected payments as paid'))
    def mark_payment_paid(self, request, queryset):
        self._mark_payment_status(queryset, Order.PaymentStatus.PAID)

    @admin.action(description=_('Mark selected payments as failed'))
    def mark_payment_failed(self, request, queryset):
        self._mark_payment_status(queryset, Order.PaymentStatus.FAILED)

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

    def _mark_payment_status(self, queryset, payment_status):
        for order in queryset:
            try:
                update_payment_status(order, payment_status)
            except Exception:
                continue
            notifications.notify_payment_status_changed(order)
