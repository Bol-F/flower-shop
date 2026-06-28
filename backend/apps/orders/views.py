from decimal import Decimal

from django.shortcuts import get_object_or_404
from django.db.models import DecimalField, ExpressionWrapper, F, Prefetch, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import IsOwnerOrAdmin
from apps.products.models import Product
from . import services
from . import notifications
from .payments import update_payment_status
from .models import DeliveryZone, Order, OrderItem
from .serializers import (
    DeliveryZoneSerializer,
    OrderSerializer,
    CreateOrderSerializer,
    UpdateOrderStatusSerializer,
    UpdatePaymentStatusSerializer,
)


def order_queryset():
    return Order.objects.select_related('user', 'delivery_zone').prefetch_related(
        Prefetch('items', queryset=OrderItem.objects.select_related('product')),
        'notification_logs',
    )


class DeliveryZoneListView(generics.ListAPIView):
    serializer_class = DeliveryZoneSerializer
    permission_classes = [permissions.AllowAny]
    queryset = DeliveryZone.objects.filter(is_active=True).order_by('name')


class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = order_queryset()
        if user.is_staff:
            return queryset
        return queryset.filter(user=user)


class CreateOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CreateOrderSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)

        order = services.create_order_from_cart(
            user=request.user,
            **serializer.validated_data,
        )
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    queryset = order_queryset()


class UpdateOrderStatusView(generics.UpdateAPIView):
    serializer_class = UpdateOrderStatusSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = Order.objects.all()
    http_method_names = ['patch']

    def patch(self, request, *args, **kwargs):
        order = self.get_object()
        serializer = self.get_serializer(order, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        notifications.notify_order_status_changed(order)
        order = order_queryset().get(pk=order.pk)
        return Response(OrderSerializer(order).data)


class UpdatePaymentStatusView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def patch(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        serializer = UpdatePaymentStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        update_payment_status(
            order,
            serializer.validated_data['payment_status'],
            payment_provider=serializer.validated_data.get('payment_provider', ''),
            payment_reference=serializer.validated_data.get('payment_reference', ''),
        )
        notifications.notify_payment_status_changed(order)
        order = order_queryset().get(pk=order.pk)
        return Response(OrderSerializer(order).data)


class AdminDashboardView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        today = timezone.localdate()
        month_start = today.replace(day=1)
        active_orders = Order.objects.exclude(status=Order.Status.CANCELLED)
        today_orders = active_orders.filter(created_at__date=today)
        month_orders = active_orders.filter(created_at__date__gte=month_start)
        delivery_queue = order_queryset().filter(
            status__in=[
                Order.Status.PENDING,
                Order.Status.CONFIRMED,
                Order.Status.PREPARING,
                Order.Status.COURIER_PICKED_UP,
            ]
        )[:10]
        low_stock_products = Product.objects.filter(
            is_available=True,
            stock__gt=0,
            stock__lte=F('low_stock_threshold'),
        ).order_by('stock', 'name')[:10]
        out_of_stock_products = Product.objects.filter(
            is_available=True,
            stock=0,
        ).order_by('name')[:10]
        unavailable_products = Product.objects.filter(
            is_available=False,
        ).order_by('name')[:10]
        best_selling = (
            OrderItem.objects.values('product_name')
            .annotate(
                quantity_sold=Sum('quantity'),
                revenue=Sum(
                    ExpressionWrapper(
                        F('product_price') * F('quantity'),
                        output_field=DecimalField(max_digits=12, decimal_places=2),
                    )
                ),
            )
            .order_by('-quantity_sold')[:10]
        )

        data = {
            'today_orders': today_orders.count(),
            'pending_orders': active_orders.filter(status=Order.Status.PENDING).count(),
            'confirmed_orders': active_orders.filter(status=Order.Status.CONFIRMED).count(),
            'preparing_orders': active_orders.filter(status=Order.Status.PREPARING).count(),
            'delivered_orders': active_orders.filter(status=Order.Status.DELIVERED).count(),
            'total_revenue_today': str(
                today_orders.aggregate(
                    total=Coalesce(
                        Sum('total_price'),
                        Value(Decimal('0.00'), output_field=DecimalField()),
                    )
                )['total']
            ),
            'total_revenue_month': str(
                month_orders.aggregate(
                    total=Coalesce(
                        Sum('total_price'),
                        Value(Decimal('0.00'), output_field=DecimalField()),
                    )
                )['total']
            ),
            'low_stock_products': [
                _product_summary(product) for product in low_stock_products
            ],
            'out_of_stock_products': [
                _product_summary(product) for product in out_of_stock_products
            ],
            'unavailable_products': [
                _product_summary(product) for product in unavailable_products
            ],
            'best_selling_products': [
                {
                    'product_name': item['product_name'],
                    'quantity_sold': item['quantity_sold'] or 0,
                    'revenue': str(item['revenue'] or 0),
                }
                for item in best_selling
            ],
            'delivery_queue': OrderSerializer(delivery_queue, many=True).data,
        }
        return Response(data)


def _product_summary(product):
    return {
        'id': product.id,
        'name': product.name,
        'slug': product.slug,
        'stock': product.stock,
        'low_stock_threshold': product.low_stock_threshold,
        'is_available': product.is_available,
        'stock_status': product.stock_status,
    }
