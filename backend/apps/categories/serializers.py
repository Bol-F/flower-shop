from rest_framework import serializers

from apps.common.serializers import AutoSlugModelSerializer

from .models import Category


class CategorySerializer(AutoSlugModelSerializer):
    product_count = serializers.SerializerMethodField()

    def get_product_count(self, obj):
        count = getattr(obj, '_product_count', None)
        if count is not None:
            return count
        return obj.products.storefront().count()

    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'description', 'image', 'product_count')
        read_only_fields = ('slug',)
