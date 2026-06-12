from django.contrib import admin
from django.db.models import Count
from django.utils.translation import gettext_lazy as _

from .models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'product_count', 'created_at')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_product_count=Count('products'))

    @admin.display(description=_('Products'), ordering='_product_count')
    def product_count(self, obj):
        return obj._product_count
