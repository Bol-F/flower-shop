from django.urls import path
from .views import (
    ChangePasswordView,
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    ProfileView,
    RegisterView,
    OAuthCallbackView,
    OAuthExchangeView,
    OAuthLinkStartView,
    OAuthProvidersView,
    OAuthStartView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token-refresh'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/password/', ChangePasswordView.as_view(), name='profile-password'),
    path('oauth/providers/', OAuthProvidersView.as_view(), name='oauth-providers'),
    path('oauth/exchange/', OAuthExchangeView.as_view(), name='oauth-exchange'),
    path('oauth/<str:provider>/start/', OAuthStartView.as_view(), name='oauth-start'),
    path('oauth/<str:provider>/link/', OAuthLinkStartView.as_view(), name='oauth-link-start'),
    path('oauth/<str:provider>/callback/', OAuthCallbackView.as_view(), name='oauth-callback'),
]
