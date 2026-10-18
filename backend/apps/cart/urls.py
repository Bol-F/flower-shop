from django.urls import path

from .views import CartView, CartItemView, GuestSelectionMergeView

urlpatterns = [
    path('', CartView.as_view(), name='cart'),
    path('merge/', GuestSelectionMergeView.as_view(), name='cart-merge'),
    path('items/', CartItemView.as_view(), name='cart-items'),
    path('items/<int:product_id>/', CartItemView.as_view(), name='cart-item-detail'),
]
