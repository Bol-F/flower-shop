from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import ScopedRateThrottle

from apps.products.serializers import ProductListSerializer

from . import services
from .serializers import (
    CartSerializer,
    AddToCartSerializer,
    UpdateCartItemSerializer,
    GuestSelectionMergeSerializer,
)


class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart = services.get_cart_for_response(request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    def delete(self, request):
        services.clear_cart(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CartItemView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        services.add_item_to_cart(
            user=request.user,
            product_id=serializer.validated_data['product_id'],
            quantity=serializer.validated_data['quantity'],
        )
        cart = services.get_cart_for_response(request.user)
        return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)

    def patch(self, request, product_id):
        serializer = UpdateCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        services.update_cart_item(
            user=request.user,
            product_id=product_id,
            quantity=serializer.validated_data['quantity'],
        )
        cart = services.get_cart_for_response(request.user)
        return Response(CartSerializer(cart).data)

    def delete(self, request, product_id):
        services.remove_item_from_cart(request.user, product_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class GuestSelectionMergeView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'cart_merge'

    def post(self, request):
        serializer = GuestSelectionMergeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        adjustments = services.merge_guest_selections(
            user=request.user, **serializer.validated_data
        )
        cart = services.get_cart_for_response(request.user)
        products = [
            item.product
            for item in request.user.wishlist_items.select_related(
                'product__category',
                'product__city',
                'product__vendor',
            )
        ]
        response = Response(
            {
                'cart': CartSerializer(cart).data,
                'wishlist': ProductListSerializer(products, many=True).data,
                **adjustments,
            }
        )
        response['Cache-Control'] = 'no-store'
        return response
