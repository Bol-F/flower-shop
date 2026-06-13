from django.urls import path

from . import views

urlpatterns = [
    path(
        'products/<slug:product_id>/',
        views.ProductSocialView.as_view(),
        name='product-social',
    ),
    path(
        'products/<slug:product_id>/review/',
        views.ReviewView.as_view(),
        name='product-review',
    ),
]
