from django.urls import path

from .views import (
    AdminDashboardView,
    DeliveryZoneListView,
    OrderListView,
    AssignCourierView,
    CreateOrderView,
    OrderDetailView,
    PayTestOrderView,
    RepeatOrderView,
    UpdateOrderStatusView,
    UpdatePaymentStatusView,
)

urlpatterns = [
    path('dashboard/', AdminDashboardView.as_view(), name='order-dashboard'),
    path('delivery-zones/', DeliveryZoneListView.as_view(), name='delivery-zone-list'),
    path('', OrderListView.as_view(), name='order-list'),
    path('create/', CreateOrderView.as_view(), name='order-create'),
    path('<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
    path('<int:pk>/pay-test/', PayTestOrderView.as_view(), name='order-pay-test'),
    path('<int:pk>/repeat/', RepeatOrderView.as_view(), name='order-repeat'),
    path('<int:pk>/status/', UpdateOrderStatusView.as_view(), name='order-status-update'),
    path('<int:pk>/courier/', AssignCourierView.as_view(), name='order-courier-assign'),
    path(
        '<int:pk>/payment-status/',
        UpdatePaymentStatusView.as_view(),
        name='order-payment-status-update',
    ),
]
