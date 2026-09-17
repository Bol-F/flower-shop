import json
from decimal import Decimal

from django.conf import settings
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Prefetch, Sum, Value
from django.db.models.functions import Coalesce, TruncDate
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.common.permissions import IsOwnerOrAdmin
from apps.marketplace.models import Courier
from apps.marketplace.services import award_loyalty_points_if_eligible, repeat_order_to_cart
from apps.products.models import Product

from . import notifications, services
from .fulfillment import assign_order_courier, change_order_status
from .models import DeliveryZone, Order, OrderItem, PaymentAttempt
from .payment_providers import get_payment_provider
from .payment_webhooks import (
    click_response,
    payme_authenticated,
    payme_error,
)
from .payments import (
    available_payment_methods,
    initialize_payment,
    pay_test_order,
    update_payment_status,
)
from .serializers import (
    AssignCourierSerializer,
    CreateOrderSerializer,
    DeliveryZoneSerializer,
    InitializePaymentSerializer,
    OrderSerializer,
    PaymentAttemptSerializer,
    UpdateOrderStatusSerializer,
    UpdatePaymentStatusSerializer,
)


def order_queryset():
    return Order.objects.select_related(
        'user',
        'city',
        'vendor',
        'assigned_courier__user',
        'delivery_zone',
        'delivery_zone__city',
        'promo_code',
    ).prefetch_related(
        Prefetch('items', queryset=OrderItem.objects.select_related('product')),
        'notification_logs',
        'payments',
    )


class DeliveryZoneListView(generics.ListAPIView):
    serializer_class = DeliveryZoneSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = DeliveryZone.objects.filter(is_active=True).select_related('city')
        city = self.request.query_params.get('city')
        if city:
            queryset = queryset.filter(city__slug=city)
        return queryset.order_by('name')


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
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'order_create'

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
        if 'status' not in serializer.validated_data:
            return Response({'status': 'A status is required.'}, status=status.HTTP_400_BAD_REQUEST)
        change_order_status(order, serializer.validated_data['status'])
        order = order_queryset().get(pk=order.pk)
        return Response(OrderSerializer(order).data)


class UpdatePaymentStatusView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def patch(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        serializer = UpdatePaymentStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = update_payment_status(
            order,
            serializer.validated_data['payment_status'],
            payment_provider=serializer.validated_data.get('payment_provider', ''),
            payment_reference=serializer.validated_data.get('payment_reference', ''),
            actor=request.user,
            reason=serializer.validated_data['reason'],
        )
        award_loyalty_points_if_eligible(order)
        notifications.notify_payment_status_changed(order)
        order = order_queryset().get(pk=order.pk)
        return Response(OrderSerializer(order).data)


class PayTestOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'test_payment'

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk, user=request.user)
        order = pay_test_order(order)
        notifications.notify_payment_status_changed(order)
        order = order_queryset().get(pk=order.pk)
        return Response(OrderSerializer(order).data)


class PaymentMethodsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({'methods': available_payment_methods()})


class InitializePaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'payment_create'

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk, user=request.user)
        serializer = InitializePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        idempotency_key = request.headers.get('Idempotency-Key') or serializer.validated_data.get(
            'idempotency_key', ''
        )
        payment, created = initialize_payment(
            order,
            provider_name=serializer.validated_data.get('provider', ''),
            idempotency_key=idempotency_key,
        )
        return Response(
            PaymentAttemptSerializer(payment).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class PaymentDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PaymentAttemptSerializer
    lookup_field = 'public_id'
    lookup_url_kwarg = 'payment_id'

    def get_queryset(self):
        queryset = PaymentAttempt.objects.select_related('order').filter(
            order_id=self.kwargs['pk'],
        )
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(order__user=self.request.user)


class PaymeWebhookView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'payment_webhook'

    def http_method_not_allowed(self, request, *args, **kwargs):
        return Response(payme_error(None, -32300, 'Only POST requests are accepted.'))

    def post(self, request):
        try:
            payload = json.loads(request.body.decode('utf-8'))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return Response(payme_error(None, -32700, 'JSON parsing error.'))
        request_id = payload.get('id') if isinstance(payload, dict) else None
        provider = get_payment_provider('payme')
        if not provider.is_configured():
            return Response(payme_error(request_id, -32504, 'Authentication failed.'))
        authorization = request.META.get('HTTP_AUTHORIZATION', '')
        if not payme_authenticated(authorization):
            return Response(payme_error(request_id, -32504, 'Authentication failed.'))
        if not settings.DEBUG and settings.PAYME_ALLOWED_IPS:
            if request.META.get('REMOTE_ADDR') not in settings.PAYME_ALLOWED_IPS:
                return Response(payme_error(request_id, -32504, 'Authentication failed.'))
        return Response(provider.handle_webhook(payload))


class ClickWebhookBaseView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    parser_classes = [FormParser]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'payment_webhook'


class ClickPrepareWebhookView(ClickWebhookBaseView):
    def post(self, request):
        provider = get_payment_provider('click')
        if not provider.is_configured():
            return Response(click_response(-8))
        return Response(provider.handle_webhook(request.data.dict()))


class ClickCompleteWebhookView(ClickWebhookBaseView):
    def post(self, request):
        provider = get_payment_provider('click')
        if not provider.is_configured():
            return Response(click_response(-8))
        return Response(provider.handle_webhook(request.data.dict()))


class AssignCourierView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def patch(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        serializer = AssignCourierSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        courier_id = serializer.validated_data.get('courier_id')
        courier = None
        if courier_id:
            courier = get_object_or_404(Courier, pk=courier_id, is_active=True)
        assign_order_courier(order, courier)
        order = order_queryset().get(pk=order.pk)
        return Response(OrderSerializer(order).data)


class RepeatOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def post(self, request, pk):
        order = get_object_or_404(order_queryset(), pk=pk)
        self.check_object_permissions(request, order)
        return Response(repeat_order_to_cart(order, request.user))


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
        revenue_by_day = (
            active_orders.annotate(day=TruncDate('created_at'))
            .values('day')
            .annotate(
                revenue=Coalesce(
                    Sum('total_price'),
                    Value(Decimal('0.00'), output_field=DecimalField()),
                ),
                orders=Count('id'),
            )
            .order_by('-day')[:14]
        )
        orders_by_status = active_orders.values('status').annotate(count=Count('id'))
        payment_status_summary = active_orders.values('payment_status').annotate(count=Count('id'))
        city_order_summary = (
            active_orders.values('city__name').annotate(count=Count('id')).order_by('-count')[:10]
        )
        top_customers = (
            active_orders.values('user__email', 'user__username')
            .annotate(
                orders=Count('id'),
                revenue=Coalesce(
                    Sum('total_price'),
                    Value(Decimal('0.00'), output_field=DecimalField()),
                ),
            )
            .order_by('-revenue')[:10]
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
            'low_stock_products': [_product_summary(product) for product in low_stock_products],
            'out_of_stock_products': [
                _product_summary(product) for product in out_of_stock_products
            ],
            'unavailable_products': [_product_summary(product) for product in unavailable_products],
            'best_selling_products': [
                {
                    'product_name': item['product_name'],
                    'quantity_sold': item['quantity_sold'] or 0,
                    'revenue': str(item['revenue'] or 0),
                }
                for item in best_selling
            ],
            'revenue_by_day': [
                {
                    'date': item['day'].isoformat() if item['day'] else None,
                    'revenue': str(item['revenue'] or 0),
                    'orders': item['orders'],
                }
                for item in revenue_by_day
            ],
            'orders_by_status': [
                {'status': item['status'], 'count': item['count']} for item in orders_by_status
            ],
            'payment_status_summary': [
                {'payment_status': item['payment_status'], 'count': item['count']}
                for item in payment_status_summary
            ],
            'city_order_summary': [
                {'city': item['city__name'] or 'Unassigned', 'count': item['count']}
                for item in city_order_summary
            ],
            'top_customers': [
                {
                    'email': item['user__email'],
                    'username': item['user__username'],
                    'orders': item['orders'],
                    'revenue': str(item['revenue'] or 0),
                }
                for item in top_customers
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
