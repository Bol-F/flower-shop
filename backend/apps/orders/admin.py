from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Order, OrderItem


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


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total_price', 'item_count', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('id', 'user__email', 'user__username', 'phone', 'shipping_address')
    list_editable = ('status',)
    list_select_related = ('user',)
    date_hierarchy = 'created_at'
    list_per_page = 25
    readonly_fields = ('user', 'total_price', 'created_at', 'updated_at')
    inlines = [OrderItemInline]

    fieldsets = (
        (None, {'fields': ('user', 'status', 'total_price')}),
        (_('Delivery'), {'fields': ('shipping_address', 'phone', 'notes')}),
        (_('Timestamps'), {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    @admin.display(description=_('Items'))
    def item_count(self, obj):
        return obj.items.count()
