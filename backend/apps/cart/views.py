from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .serializers import (
    CartSerializer,
    AddToCartSerializer,
    UpdateCartItemSerializer,
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

        cart_item = services.add_item_to_cart(
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
