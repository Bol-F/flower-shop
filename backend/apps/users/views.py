import hashlib
import secrets
from datetime import timedelta
from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qsl

from django.conf import settings
from django.db import transaction
from django.shortcuts import redirect
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    ChangePasswordSerializer,
    RegisterSerializer,
    UserProfileSerializer,
    CustomTokenObtainPairSerializer,
)
from .models import OAuthExchangeCode
from .oauth import (
    OAuthError,
    configured_providers,
    consume_login_attempt,
    create_login_attempt,
    exchange_provider_code,
    resolve_social_user,
)


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth_register'

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            UserProfileSerializer(user).data,
            status=status.HTTP_201_CREATED,
        )


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth_login'


class CustomTokenRefreshView(TokenRefreshView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth_refresh'


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(generics.GenericAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth_password'

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


def _frontend_callback(**params):
    parts = urlsplit(settings.OAUTH_FRONTEND_CALLBACK_URL)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query.update({key: value for key, value in params.items() if value is not None})
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), ''))


def _frontend_path(path: str, **params):
    parts = urlsplit(f'{settings.FRONTEND_URL.rstrip("/")}{path}')
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query.update({key: value for key, value in params.items() if value is not None})
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


class OAuthProvidersView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        enabled = set(configured_providers())
        return Response(
            {
                'providers': [
                    {'id': provider, 'enabled': provider in enabled}
                    for provider in ('google', 'github', 'microsoft')
                ],
            }
        )


class OAuthStartView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth_oauth_start'

    def get(self, request, provider):
        try:
            _, _, authorization_url = create_login_attempt(
                provider,
                next_path=request.query_params.get('next', '/profile'),
            )
        except OAuthError as exc:
            return redirect(_frontend_callback(error=exc.code, message=exc.message))
        return redirect(authorization_url)


class OAuthLinkStartView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth_oauth_start'

    def post(self, request, provider):
        try:
            _, _, authorization_url = create_login_attempt(
                provider,
                next_path='/profile',
                linking_user=request.user,
            )
        except OAuthError as exc:
            return Response({'code': exc.code, 'detail': exc.message}, status=400)
        return Response({'authorization_url': authorization_url})


class OAuthCallbackView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth_oauth_callback'

    def get(self, request, provider):
        provider_error = request.query_params.get('error')
        if provider_error:
            return redirect(_frontend_callback(error='cancelled', message='Sign-in was cancelled.'))
        try:
            attempt = consume_login_attempt(provider, request.query_params.get('state', ''))
            try:
                identity = exchange_provider_code(
                    provider,
                    request.query_params.get('code', ''),
                    attempt,
                )
            finally:
                attempt.code_verifier = ''
                attempt.nonce = ''
                attempt.save(update_fields=('code_verifier', 'nonce'))
            user = resolve_social_user(provider, identity, linking_user=attempt.linking_user)
            if attempt.linking_user_id:
                return redirect(_frontend_path(attempt.next_path, connected=provider))
            raw_code = secrets.token_urlsafe(48)
            OAuthExchangeCode.objects.create(
                user=user,
                token_digest=hashlib.sha256(raw_code.encode('utf-8')).hexdigest(),
                expires_at=timezone.now() + timedelta(seconds=settings.OAUTH_EXCHANGE_TTL_SECONDS),
            )
            return redirect(_frontend_callback(code=raw_code, next=attempt.next_path))
        except OAuthError as exc:
            return redirect(_frontend_callback(error=exc.code, message=exc.message))
        except Exception:
            return redirect(
                _frontend_callback(
                    error='oauth_failed',
                    message='Sign-in could not be completed. Please try again.',
                )
            )


class OAuthExchangeView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth_oauth_exchange'

    @transaction.atomic
    def post(self, request):
        raw_code = str(request.data.get('code') or '')
        digest = hashlib.sha256(raw_code.encode('utf-8')).hexdigest()
        exchange = (
            OAuthExchangeCode.objects.select_for_update()
            .select_related('user')
            .filter(token_digest=digest)
            .first()
        )
        if (
            not raw_code
            or exchange is None
            or exchange.used_at is not None
            or exchange.expires_at <= timezone.now()
        ):
            return Response(
                {'code': 'invalid_exchange', 'detail': 'This sign-in code is invalid or expired.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        exchange.used_at = timezone.now()
        exchange.save(update_fields=('used_at',))
        refresh = RefreshToken.for_user(exchange.user)
        return Response(
            {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserProfileSerializer(exchange.user).data,
            }
        )
