from rest_framework import serializers

from apps.categories.models import Category
from apps.categories.serializers import CategorySerializer
from .models import Product


class ProductListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    stock_quantity = serializers.IntegerField(source='stock', read_only=True)

    class Meta:
        model = Product
        fields = (
            'id', 'name', 'slug', 'price', 'image',
            'category', 'category_name', 'stock_quantity',
            'is_available', 'is_in_stock',
            'is_low_stock', 'stock_status',
        )


class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    stock_quantity = serializers.IntegerField(source='stock', read_only=True)
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
            'is_low_stock', 'stock_status', 'created_at', 'updated_at',
        )
        read_only_fields = ('slug', 'created_at', 'updated_at')
