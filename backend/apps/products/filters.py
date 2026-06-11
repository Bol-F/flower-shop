import django_filters

from .models import Product


class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    category = django_filters.CharFilter(field_name='category__slug')
    is_available = django_filters.BooleanFilter()

    class Meta:
        model = Product
        fields = ['min_price', 'max_price', 'category', 'is_available']
