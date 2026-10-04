from django.db.models import Avg, Count, FloatField, IntegerField, OuterRef, Subquery, Value
from django.db.models.functions import Coalesce
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter

from apps.common.permissions import IsAdminOrReadOnly
from apps.reviews.models import Review

from .models import Product
from .filters import ProductFilter
from .serializers import ProductDetailSerializer, ProductListSerializer


def product_queryset():
    review_stats = (
        Review.objects.filter(product=OuterRef('slug'))
        .values('product')
        .annotate(average=Avg('rating'), count=Count('id'))
    )
    return Product.objects.select_related('category', 'city', 'vendor').annotate(
        rating_average=Subquery(
            review_stats.values('average')[:1],
            output_field=FloatField(),
        ),
        rating_count=Coalesce(
            Subquery(review_stats.values('count')[:1], output_field=IntegerField()),
            Value(0),
        ),
    )


class ProductViewSet(viewsets.ModelViewSet):
    queryset = product_queryset().filter(is_available=True)
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'description', 'category__name']
    ordering_fields = ['price', 'created_at', 'name']
    ordering = ['-created_at']

    def get_queryset(self):
        if self.request.user and self.request.user.is_staff:
            return product_queryset()
        return product_queryset().filter(is_available=True)

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        return ProductDetailSerializer
