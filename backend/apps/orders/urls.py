from django.urls import path

from .views import (
    AdminDashboardView,
    DeliveryZoneListView,
    OrderListView,
    CreateOrderView,
    OrderDetailView,
    UpdateOrderStatusView,
    UpdatePaymentStatusView,
)

urlpatterns = [
    path('dashboard/', AdminDashboardView.as_view(), name='order-dashboard'),
    path('delivery-zones/', DeliveryZoneListView.as_view(), name='delivery-zone-list'),
    path('', OrderListView.as_view(), name='order-list'),
    path('create/', CreateOrderView.as_view(), name='order-create'),
    path('<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
    path('<int:pk>/status/', UpdateOrderStatusView.as_view(), name='order-status-update'),
    path(
        '<int:pk>/payment-status/',
        UpdatePaymentStatusView.as_view(),
        name='order-payment-status-update',
    ),
]
