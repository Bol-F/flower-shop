from rest_framework import viewsets
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from apps.common.permissions import IsAdminOrReadOnly
from .models import Product
from .serializers import ProductListSerializer, ProductDetailSerializer
from .filters import ProductFilter


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related('category', 'city', 'vendor').filter(is_available=True)
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'description', 'category__name']
    ordering_fields = ['price', 'created_at', 'name']
    ordering = ['-created_at']

    def get_queryset(self):
        if self.request.user and self.request.user.is_staff:
            return Product.objects.select_related('category', 'city', 'vendor').all()
        return Product.objects.select_related('category', 'city', 'vendor').filter(is_available=True)

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        return ProductDetailSerializer
