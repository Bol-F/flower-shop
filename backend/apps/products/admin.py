from typing import ClassVar

from django.contrib import admin
from django.db.models import F
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import Product


class StockLevelFilter(admin.SimpleListFilter):
    title = _('stock level')
    parameter_name = 'stock_level'

    def lookups(self, request, model_admin):
        return (
            ('low', _('Needs restocking')),
            ('in_stock', _('Healthy stock')),
            ('out_of_stock', _('Out of stock')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'low':
            return queryset.filter(is_available=True, stock__lte=F('low_stock_threshold'))
        if self.value() == 'in_stock':
            return queryset.filter(is_available=True, stock__gt=F('low_stock_threshold'))
        if self.value() == 'out_of_stock':
            return queryset.filter(stock=0)
        return queryset


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'thumbnail',
        'name',
        'category',
        'price',
        'stock',
        'stock_status',
        'is_available',
    )
    list_display_links = ('thumbnail', 'name')
    list_filter = (StockLevelFilter, 'category', 'city', 'vendor', 'is_available', 'created_at')
    search_fields = ('name', 'description', 'slug', 'vendor__name')
    search_help_text = _('Find flowers by name, description, slug, or florist.')
    prepopulated_fields: ClassVar[dict] = {'slug': ('name',)}
    list_editable = ('price', 'stock', 'is_available')
    list_select_related = ('category', 'city', 'vendor')
    date_hierarchy = 'created_at'
    list_per_page = 25
    readonly_fields = ('preview', 'created_at', 'updated_at')

    fieldsets = (
        (None, {'fields': ('name', 'slug', 'category', 'city', 'vendor', 'description')}),
        (
            _('Pricing & stock'),
            {
                'fields': ('price', 'stock', 'low_stock_threshold', 'is_available'),
            },
        ),
        (_('Image'), {'fields': ('image', 'preview')}),
        (_('Timestamps'), {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    @admin.display(description=_('Image'))
    def thumbnail(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" class="flower-product-thumb" width="48" height="48" '
                'loading="lazy" alt="{}">',
                obj.image.url,
                obj.name,
            )
        return format_html(
            '<span class="flower-product-placeholder" role="img" aria-label="{}">'
            '<svg class="flower-icon" width="24" height="24" viewBox="0 0 24 24" '
            'fill="none" stroke="currentColor" stroke-width="1.6" '
            'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
            '<path d="M12 6a3 3 0 0 1 5.2 3 3 3 0 0 1 0 6 '
            '3 3 0 0 1-5.2 3 3 3 0 0 1-5.2-3 '
            '3 3 0 0 1 0-6A3 3 0 0 1 12 6Z"/>'
            '<circle cx="12" cy="12" r="3"/></svg></span>',
            _('No flower photo'),
        )

    @admin.display(description=_('Stock status'), ordering='stock')
    def stock_status(self, obj):
        statuses = {
            'in_stock': ('success', _('In stock')),
            'low_stock': ('warning', _('Low stock')),
            'out_of_stock': ('danger', _('Out of stock')),
            'unavailable': ('neutral', _('Hidden')),
        }
        tone, label = statuses[obj.stock_status]
        return format_html('<span class="flower-badge flower-badge--{}">{}</span>', tone, label)

    @admin.display(description=_('Preview'))
    def preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width:300px;width:100%;height:auto;'
                'border-radius:16px;" alt="{}">',
                obj.image.url,
                obj.name,
            )
        return _('Add a flower photo to help your team recognize this product.')
