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
    ClickCompleteWebhookView,
    ClickPrepareWebhookView,
    InitializePaymentView,
    PaymentDetailView,
    PaymentMethodsView,
    PaymeWebhookView,
)

urlpatterns = [
    path('dashboard/', AdminDashboardView.as_view(), name='order-dashboard'),
    path('delivery-zones/', DeliveryZoneListView.as_view(), name='delivery-zone-list'),
    path('payment-methods/', PaymentMethodsView.as_view(), name='payment-methods'),
    path('payments/payme/webhook/', PaymeWebhookView.as_view(), name='payme-webhook'),
    path('payments/click/prepare/', ClickPrepareWebhookView.as_view(), name='click-prepare'),
    path('payments/click/complete/', ClickCompleteWebhookView.as_view(), name='click-complete'),
    path('', OrderListView.as_view(), name='order-list'),
    path('create/', CreateOrderView.as_view(), name='order-create'),
    path('<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
    path('<int:pk>/pay-test/', PayTestOrderView.as_view(), name='order-pay-test'),
    path('<int:pk>/payments/', InitializePaymentView.as_view(), name='payment-initialize'),
    path(
        '<int:pk>/payments/<uuid:payment_id>/',
        PaymentDetailView.as_view(),
        name='payment-detail',
    ),
    path('<int:pk>/repeat/', RepeatOrderView.as_view(), name='order-repeat'),
    path('<int:pk>/status/', UpdateOrderStatusView.as_view(), name='order-status-update'),
    path('<int:pk>/courier/', AssignCourierView.as_view(), name='order-courier-assign'),
    path(
        '<int:pk>/payment-status/',
        UpdatePaymentStatusView.as_view(),
        name='order-payment-status-update',
    ),
]
