from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('subtotal',)
    autocomplete_fields = ('product',)

    @admin.display(description=_('Subtotal'))
    def subtotal(self, obj):
        return obj.subtotal


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'item_total', 'price_total', 'updated_at')
    search_fields = ('user__email', 'user__username')
    list_select_related = ('user',)
    readonly_fields = ('user', 'created_at', 'updated_at')
    inlines = [CartItemInline]

    @admin.display(description=_('Total items'))
    def item_total(self, obj):
        return obj.total_items

    @admin.display(description=_('Total price'))
    def price_total(self, obj):
        return obj.total_price
