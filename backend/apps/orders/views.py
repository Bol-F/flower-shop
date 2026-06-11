from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import IsOwnerOrAdmin
from . import services
from .models import Order
from .serializers import OrderSerializer, CreateOrderSerializer, UpdateOrderStatusSerializer


class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Order.objects.prefetch_related('items').all()
        return Order.objects.prefetch_related('items').filter(user=user)


class CreateOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CreateOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order = services.create_order_from_cart(
            user=request.user,
            **serializer.validated_data,
        )
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    queryset = Order.objects.prefetch_related('items').all()


class UpdateOrderStatusView(generics.UpdateAPIView):
    serializer_class = UpdateOrderStatusSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = Order.objects.all()
    http_method_names = ['patch']
