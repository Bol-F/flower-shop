from rest_framework import serializers

from .models import Category


class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(source='products.count', read_only=True)

    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'description', 'image', 'product_count')
        read_only_fields = ('slug',)
