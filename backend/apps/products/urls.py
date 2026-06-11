from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ProductViewSet

router = DefaultRouter()
router.register('', ProductViewSet, basename='product')

urlpatterns = [
    path('', include(router.urls)),
]
