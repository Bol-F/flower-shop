from django.urls import path

from .views import OrderListView, CreateOrderView, OrderDetailView, UpdateOrderStatusView

urlpatterns = [
    path('', OrderListView.as_view(), name='order-list'),
    path('create/', CreateOrderView.as_view(), name='order-create'),
    path('<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
    path('<int:pk>/status/', UpdateOrderStatusView.as_view(), name='order-status-update'),
]
