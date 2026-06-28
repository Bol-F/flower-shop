import django_filters

from .models import Product


class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    category = django_filters.CharFilter(field_name='category__slug')
    city = django_filters.CharFilter(field_name='city__slug')
    vendor = django_filters.CharFilter(field_name='vendor__slug')
    is_available = django_filters.BooleanFilter()

    class Meta:
        model = Product
        fields = ['min_price', 'max_price', 'category', 'city', 'vendor', 'is_available']
