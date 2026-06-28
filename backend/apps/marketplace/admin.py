from django.contrib import admin

from .models import City, Courier, PromoCode, Vendor, WishlistItem


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'country', 'currency', 'default_delivery_fee',
        'free_delivery_threshold', 'is_active',
    )
    list_filter = ('country', 'currency', 'is_active')
    search_fields = ('name', 'country', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_active', 'default_delivery_fee', 'free_delivery_threshold')


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'phone', 'commission_percent', 'is_active', 'created_at')
    list_filter = ('city', 'is_active')
    search_fields = ('name', 'slug', 'phone', 'address')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('commission_percent', 'is_active')


@admin.register(Courier)
class CourierAdmin(admin.ModelAdmin):
    list_display = ('user', 'city', 'phone', 'current_status', 'is_active')
    list_filter = ('city', 'current_status', 'is_active')
    search_fields = ('user__email', 'user__username', 'phone')
    list_editable = ('current_status', 'is_active')


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = (
        'code', 'discount_type', 'discount_value', 'min_order_amount',
        'max_discount_amount', 'used_count', 'usage_limit', 'is_active',
    )
    list_filter = ('discount_type', 'is_active', 'valid_from', 'valid_until')
    search_fields = ('code',)
    list_editable = ('is_active',)


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'created_at')
    search_fields = ('user__email', 'product__name', 'product__slug')
    list_select_related = ('user', 'product')
