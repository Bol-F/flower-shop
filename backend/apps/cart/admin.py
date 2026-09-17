from decimal import Decimal

from django.contrib import admin
from django.db.models import DecimalField, F, IntegerField, Sum, Value
from django.db.models.functions import Coalesce
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

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product')


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'item_total', 'price_total', 'updated_at')
    search_fields = ('user__email', 'user__username')
    list_select_related = ('user',)
    readonly_fields = ('user', 'created_at', 'updated_at')
    inlines = (CartItemInline,)

    def has_add_permission(self, request):
        return False

    def get_queryset(self, request):
        price_field = DecimalField(max_digits=18, decimal_places=2)
        return (
            super()
            .get_queryset(request)
            .annotate(
                _admin_total_items=Coalesce(
                    Sum('items__quantity'),
                    Value(0),
                    output_field=IntegerField(),
                ),
                _admin_total_price=Coalesce(
                    Sum(
                        F('items__product__price') * F('items__quantity'), output_field=price_field
                    ),
                    Value(Decimal('0.00'), output_field=price_field),
                    output_field=price_field,
                ),
            )
        )

    @admin.display(description=_('Total items'), ordering='_admin_total_items')
    def item_total(self, obj):
        return obj._admin_total_items

    @admin.display(description=_('Total price'), ordering='_admin_total_price')
    def price_total(self, obj):
        return obj._admin_total_price
