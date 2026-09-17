from typing import ClassVar

from django.contrib import admin
from django.db.models import F, Q
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import City, Courier, PromoCode, Vendor, WishlistItem


class PromoAvailabilityFilter(admin.SimpleListFilter):
    title = _('availability')
    parameter_name = 'availability'

    def lookups(self, request, model_admin):
        return (
            ('available', _('Usable now')),
            ('scheduled', _('Scheduled')),
            ('expired', _('Expired')),
            ('exhausted', _('Usage limit reached')),
            ('disabled', _('Disabled')),
        )

    def queryset(self, request, queryset):
        value = self.value()
        now = timezone.now()
        if value == 'disabled':
            return queryset.filter(is_active=False)
        if value == 'scheduled':
            return queryset.filter(is_active=True, valid_from__gt=now)
        if value == 'expired':
            return queryset.filter(is_active=True, valid_from__lte=now, valid_until__lt=now)
        current = queryset.filter(is_active=True, valid_from__lte=now).filter(
            Q(valid_until__isnull=True) | Q(valid_until__gte=now)
        )
        if value == 'exhausted':
            return current.filter(usage_limit__isnull=False, used_count__gte=F('usage_limit'))
        if value == 'available':
            return current.filter(Q(usage_limit__isnull=True) | Q(used_count__lt=F('usage_limit')))
        return queryset


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'country',
        'currency',
        'default_delivery_fee',
        'free_delivery_threshold',
        'is_active',
    )
    list_filter = ('country', 'currency', 'is_active')
    search_fields = ('name', 'country', 'slug')
    prepopulated_fields: ClassVar[dict] = {'slug': ('name',)}
    list_editable = ('is_active', 'default_delivery_fee', 'free_delivery_threshold')
    list_per_page = 25


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'phone', 'commission_percent', 'is_active', 'created_at')
    list_filter = ('city', 'is_active')
    search_fields = ('name', 'slug', 'phone', 'address')
    prepopulated_fields: ClassVar[dict] = {'slug': ('name',)}
    list_editable = ('commission_percent', 'is_active')
    list_select_related = ('city',)
    autocomplete_fields = ('city',)
    list_per_page = 25


@admin.register(Courier)
class CourierAdmin(admin.ModelAdmin):
    list_display = ('user', 'city', 'phone', 'current_status', 'is_active')
    list_filter = ('city', 'current_status', 'is_active')
    search_fields = ('user__email', 'user__username', 'phone')
    list_editable = ('current_status', 'is_active')
    list_select_related = ('user', 'city')
    autocomplete_fields = ('user', 'city')
    list_per_page = 25


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'discount_type',
        'discount_value',
        'min_order_amount',
        'max_discount_amount',
        'used_count',
        'usage_limit',
        'availability_badge',
        'is_active',
    )
    list_filter = (
        PromoAvailabilityFilter,
        'discount_type',
        'is_active',
        'valid_from',
        'valid_until',
    )
    search_fields = ('code',)
    list_editable = ('is_active',)
    readonly_fields = ('used_count', 'created_at')
    list_per_page = 25

    @admin.display(description=_('Usability'))
    def availability_badge(self, obj):
        now = timezone.now()
        if not obj.is_active:
            tone, label = 'neutral', _('Disabled')
        elif obj.valid_from > now:
            tone, label = 'neutral', _('Scheduled')
        elif obj.valid_until and obj.valid_until < now:
            tone, label = 'danger', _('Expired')
        elif obj.usage_limit is not None and obj.used_count >= obj.usage_limit:
            tone, label = 'warning', _('Usage limit reached')
        else:
            tone, label = 'success', _('Usable now')
        return format_html('<span class="flower-badge flower-badge--{}">{}</span>', tone, label)


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'created_at')
    search_fields = ('user__email', 'product__name', 'product__slug')
    list_select_related = ('user', 'product')
    autocomplete_fields = ('user', 'product')
    list_filter = ('created_at',)
    list_per_page = 25
