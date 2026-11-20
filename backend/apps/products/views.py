from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter

from apps.common.permissions import IsAdminOrReadOnly, staff_has_model_permissions

from .models import Product
from .filters import ProductFilter
from .serializers import ProductDetailSerializer, ProductListSerializer


def product_queryset():
    return Product.objects.select_related('category', 'city', 'vendor').with_review_stats()


class ProductViewSet(viewsets.ModelViewSet):
    queryset = product_queryset().storefront()
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'description', 'category__name']
    ordering_fields = ['price', 'created_at', 'name']
    ordering = ['-created_at']

    def get_queryset(self):
        if staff_has_model_permissions(self.request.user, 'products.view_product'):
            return product_queryset()
        return product_queryset().storefront()

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        return ProductDetailSerializer
