from django.urls import path

from .views import (
    CityListView,
    CourierListView,
    PromoValidateView,
    VendorListView,
    WishlistItemDeleteView,
    WishlistView,
)

urlpatterns = [
    path('cities/', CityListView.as_view(), name='marketplace-city-list'),
    path('vendors/', VendorListView.as_view(), name='marketplace-vendor-list'),
    path('couriers/', CourierListView.as_view(), name='marketplace-courier-list'),
    path('promo-codes/validate/', PromoValidateView.as_view(), name='promo-validate'),
    path('wishlist/', WishlistView.as_view(), name='wishlist'),
    path('wishlist/<int:product_id>/', WishlistItemDeleteView.as_view(), name='wishlist-delete'),
]
