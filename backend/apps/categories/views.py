from django.db.models import Count, Q
from rest_framework import viewsets

from apps.common.permissions import IsAdminOrReadOnly, staff_has_model_permissions
from apps.products.models import Product
from .models import Category
from .serializers import CategorySerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'slug'

    def get_queryset(self):
        if staff_has_model_permissions(self.request.user, 'products.view_product'):
            return Category.objects.annotate(_product_count=Count('products')).order_by(
                'name', 'pk'
            )
        return Category.objects.annotate(
            _product_count=Count('products', filter=Q(products__in=Product.objects.storefront()))
        ).order_by('name', 'pk')
