from rest_framework import serializers

from apps.categories.models import Category
from apps.categories.serializers import CategorySerializer
from .models import Product


class ProductListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    city_name = serializers.CharField(source='city.name', read_only=True)
    city_slug = serializers.CharField(source='city.slug', read_only=True)
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    vendor_slug = serializers.CharField(source='vendor.slug', read_only=True)
    stock_quantity = serializers.IntegerField(source='stock', read_only=True)

    class Meta:
        model = Product
        fields = (
            'id', 'name', 'slug', 'price', 'image',
            'category', 'category_name', 'stock_quantity',
            'city_name', 'city_slug', 'vendor_name', 'vendor_slug',
            'is_available', 'is_in_stock',
            'is_low_stock', 'stock_status',
        )


class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    stock_quantity = serializers.IntegerField(source='stock', read_only=True)
    city_name = serializers.CharField(source='city.name', read_only=True)
    city_slug = serializers.CharField(source='city.slug', read_only=True)
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    vendor_slug = serializers.CharField(source='vendor.slug', read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        source='category',
        queryset=Category.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Product
        fields = (
            'id', 'name', 'slug', 'description', 'price',
            'category', 'category_id', 'image', 'stock',
            'stock_quantity', 'low_stock_threshold', 'is_available', 'is_in_stock',
            'is_low_stock', 'stock_status', 'city_name', 'city_slug',
            'vendor_name', 'vendor_slug', 'created_at', 'updated_at',
        )
        read_only_fields = ('slug', 'created_at', 'updated_at')
