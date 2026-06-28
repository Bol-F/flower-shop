from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import City, Courier, Vendor, WishlistItem
from .serializers import (
    CitySerializer,
    CourierSerializer,
    PromoValidationSerializer,
    VendorSerializer,
    WishlistItemSerializer,
)


class CityListView(generics.ListAPIView):
    serializer_class = CitySerializer
    permission_classes = [permissions.AllowAny]
    queryset = City.objects.filter(is_active=True).order_by('name')


class VendorListView(generics.ListAPIView):
    serializer_class = VendorSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Vendor.objects.filter(is_active=True).select_related('city')


class CourierListView(generics.ListAPIView):
    serializer_class = CourierSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = Courier.objects.filter(is_active=True).select_related('user', 'city')


class PromoValidateView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PromoValidationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        promo = serializer.validated_data['promo']
        return Response(
            {
                'code': promo.code,
                'discount_type': promo.discount_type,
                'discount_value': str(promo.discount_value),
                'discount_amount': f"{serializer.validated_data['discount']:.2f}",
            }
        )


class WishlistView(generics.ListCreateAPIView):
    serializer_class = WishlistItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return WishlistItem.objects.filter(user=self.request.user).select_related(
            'product', 'product__category',
        )

    def get_serializer_context(self):
        return {'request': self.request}


class WishlistItemDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, product_id):
        WishlistItem.objects.filter(user=request.user, product_id=product_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
