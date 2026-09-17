from django import forms
from django.contrib import admin, messages
from django.contrib.admin import helpers
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.template.response import TemplateResponse
from django.urls import path
from django.utils import timezone
from django.utils.formats import date_format
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from apps.marketplace.models import Courier
from apps.marketplace.services import award_loyalty_points_if_eligible

from . import notifications
from .fulfillment import assign_order_courier, change_order_status
from .models import DeliveryZone, NotificationLog, Order, OrderItem, PaymentAttempt, PaymentEvent
from .payments import update_payment_status


class AssignCourierForm(forms.Form):
    courier = forms.ModelChoiceField(
        label=_('On-duty courier'),
        queryset=Courier.objects.filter(is_active=True)
        .exclude(current_status=Courier.Status.OFFLINE)
        .select_related('user', 'city'),
    )


class OrderAdminForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = '__all__'

    def clean(self):
        cleaned = super().clean()
        delivery_date = cleaned.get('delivery_date')
        if (
            'delivery_date' in self.changed_data
            and delivery_date
            and delivery_date < timezone.localdate()
        ):
            self.add_error('delivery_date', _('Delivery date cannot be in the past.'))
        if {'delivery_lat', 'delivery_lng'} & set(self.changed_data):
            lat = cleaned.get('delivery_lat')
            lng = cleaned.get('delivery_lng')
            if (lat is None) != (lng is None):
                self.add_error('delivery_lat', _('Set both map coordinates, or clear both.'))
        return cleaned


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

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    change_list_template = 'admin/orders/order/change_list.html'
    form = OrderAdminForm
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
    list_select_related = ('user', 'city', 'vendor', 'assigned_courier', 'delivery_zone')
    date_hierarchy = 'created_at'
    list_per_page = 25
    readonly_fields = (
        'user',
        'city',
        'vendor',
        'status',
        'payment_method',
        'promo_code',
        'delivery_zone',
        'delivery_requires_confirmation',
        'assigned_courier',
        'courier_assigned_at',
        'courier_picked_up_at',
        'delivered_at',
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
        'assign_courier',
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

    def has_add_permission(self, request):
        """Orders must reserve inventory and calculate totals through checkout."""
        return False

    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        if obj and obj.status in (Order.Status.DELIVERED, Order.Status.CANCELLED):
            return (
                *fields,
                'delivery_date',
                'delivery_time_slot',
                'delivery_address',
                'delivery_lat',
                'delivery_lng',
                'shipping_address',
                'phone',
                'recipient_name',
                'recipient_phone',
                'gift_note',
                'call_recipient_before_delivery',
            )
        return fields

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
        if not self.has_module_permission(request) or not self.has_view_or_change_permission(
            request
        ):
            raise PermissionDenied

        orders = (
            self.get_queryset(request)
            .select_related('user')
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

    @admin.action(description=_('Mark selected cash orders as paid'), permissions=['change'])
    def mark_cash_paid(self, request, queryset):
        updated = 0
        skipped = []
        for order in queryset.select_related('user'):
            if (
                order.payment_method != Order.PaymentMethod.CASH
                or order.payment_status == Order.PaymentStatus.PAID
            ):
                skipped.append(order.id)
                continue
            try:
                order = update_payment_status(
                    order,
                    Order.PaymentStatus.PAID,
                    payment_provider='cash',
                    actor=request.user,
                    reason=_('Cash payment recorded in Django administration.'),
                )
            except ValidationError:
                skipped.append(order.id)
                continue
            award_loyalty_points_if_eligible(order)
            notifications.notify_payment_status_changed(order)
            self.log_change(request, order, _('Cash payment marked paid'))
            updated += 1
        self._action_feedback(request, updated, skipped, _('Cash payment recorded'))

    @admin.action(
        description=_('Assign an on-duty courier to selected orders'), permissions=['change']
    )
    def assign_courier(self, request, queryset):
        selected_ids = list(queryset.values_list('pk', flat=True))
        if not selected_ids:
            return None
        if len(selected_ids) > 200:
            self.message_user(request, _('Select at most 200 orders at a time.'), messages.ERROR)
            return None
        form = AssignCourierForm(request.POST if 'apply' in request.POST else None)
        if 'apply' in request.POST and form.is_valid():
            courier = form.cleaned_data['courier']
            updated = 0
            skipped = []
            for order in queryset:
                try:
                    order, changed = assign_order_courier(order, courier)
                except ValidationError:
                    skipped.append(order.id)
                    continue
                if changed:
                    self.log_change(request, order, _('Courier assigned'))
                    updated += 1
                else:
                    skipped.append(order.id)
            self._action_feedback(request, updated, skipped, _('Courier assigned'))
            return None
        context = {
            **self.admin_site.each_context(request),
            'title': _('Assign courier'),
            'opts': self.model._meta,
            'form': form,
            'orders': queryset,
            'selected_ids': selected_ids,
            'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
        }
        return TemplateResponse(request, 'admin/orders/order/assign_courier.html', context)

    @admin.action(description=_('Mark selected orders as confirmed'), permissions=['change'])
    def mark_confirmed(self, request, queryset):
        self._mark_status(request, queryset, Order.Status.CONFIRMED)

    @admin.action(description=_('Mark selected orders as preparing'), permissions=['change'])
    def mark_preparing(self, request, queryset):
        self._mark_status(request, queryset, Order.Status.PREPARING)

    @admin.action(
        description=_('Mark selected orders as courier picked up'), permissions=['change']
    )
    def mark_courier_picked_up(self, request, queryset):
        self._mark_status(request, queryset, Order.Status.COURIER_PICKED_UP)

    @admin.action(description=_('Mark selected orders as delivered'), permissions=['change'])
    def mark_delivered(self, request, queryset):
        self._mark_status(request, queryset, Order.Status.DELIVERED)

    def _mark_status(self, request, queryset, status):
        updated = 0
        skipped = []
        for order in queryset:
            try:
                order, changed = change_order_status(order, status)
            except ValidationError:
                skipped.append(order.id)
                continue
            if changed:
                self.log_change(
                    request,
                    order,
                    _('Fulfillment status changed to %(status)s')
                    % {'status': order.get_status_display()},
                )
                updated += 1
            else:
                skipped.append(order.id)
        self._action_feedback(request, updated, skipped, _('Fulfillment status updated'))

    def _action_feedback(self, request, updated, skipped, action):
        if updated:
            self.message_user(
                request,
                _('%(action)s for %(count)d order(s).') % {'action': action, 'count': updated},
                messages.SUCCESS,
            )
        if skipped:
            sample = ', '.join(str(pk) for pk in skipped[:5])
            self.message_user(
                request,
                _(
                    '%(count)d order(s) skipped (including #%(sample)s): already updated or ineligible.'
                )
                % {'count': len(skipped), 'sample': sample},
                messages.WARNING,
            )


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
