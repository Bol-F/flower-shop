from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.common.permissions import staff_has_model_permissions
from apps.products.models import Product

from .models import Review
from .serializers import ReviewSerializer, ReviewWriteSerializer


def product_summary(product_id, request):
    """Everything the product page needs in one payload: the rating
    aggregate, the caller's own review and the full comment list."""
    reviews = Review.objects.filter(product=product_id).select_related('user')
    agg = reviews.aggregate(average=Avg('rating'), count=Count('id'))

    my_review = None
    user = getattr(request, 'user', None)
    if user and user.is_authenticated:
        mine = reviews.filter(user=user).first()
        if mine:
            my_review = {'rating': mine.rating, 'body': mine.body}

    return {
        'product': product_id,
        'rating_average': round(agg['average'], 1) if agg['average'] else None,
        'rating_count': agg['count'],
        'my_review': my_review,
        'reviews': ReviewSerializer(reviews, many=True, context={'request': request}).data,
    }


def require_catalog_product(product_id, request):
    products = Product.objects.all()
    if not staff_has_model_permissions(request.user, 'products.view_product'):
        products = products.storefront()
    return get_object_or_404(products, slug=product_id)


class ProductSocialView(APIView):
    """GET the public summary of ratings + comments for a product.
    Readable by anyone; write actions live on the sibling endpoint."""

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, product_id):
        require_catalog_product(product_id, request)
        return Response(product_summary(product_id, request))


class ReviewView(APIView):
    """Create/update (POST) or remove (DELETE) the caller's own review."""

    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'review_write'

    def post(self, request, product_id):
        require_catalog_product(product_id, request)
        serializer = ReviewWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        Review.objects.update_or_create(
            user=request.user,
            product=product_id,
            defaults=serializer.validated_data,
        )
        return Response(product_summary(product_id, request), status=status.HTTP_201_CREATED)

    def delete(self, request, product_id):
        require_catalog_product(product_id, request)
        Review.objects.filter(user=request.user, product=product_id).delete()
        return Response(product_summary(product_id, request))
