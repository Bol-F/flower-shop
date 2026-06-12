from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('thumbnail', 'name', 'category', 'price', 'stock', 'is_available', 'created_at')
    list_display_links = ('thumbnail', 'name')
    list_filter = ('category', 'is_available', 'created_at')
    search_fields = ('name', 'description', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('price', 'stock', 'is_available')
    list_select_related = ('category',)
    date_hierarchy = 'created_at'
    list_per_page = 25
    readonly_fields = ('preview', 'created_at', 'updated_at')

    fieldsets = (
        (None, {'fields': ('name', 'slug', 'category', 'description')}),
        (_('Pricing & stock'), {'fields': ('price', 'stock', 'is_available')}),
        (_('Image'), {'fields': ('image', 'preview')}),
        (_('Timestamps'), {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    @admin.display(description=_('Image'))
    def thumbnail(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:42px;height:42px;object-fit:cover;'
                'border-radius:6px;" alt="">', obj.image.url)
        return '🌸'

    @admin.display(description=_('Preview'))
    def preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width:300px;border-radius:10px;" alt="">',
                obj.image.url)
        return '—'
