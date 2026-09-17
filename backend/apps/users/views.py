import hashlib
import logging
import secrets
from datetime import timedelta
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django.conf import settings
from django.db import transaction
from django.shortcuts import redirect
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import OAuthExchangeCode, OAuthLinkExchangeCode
from .oauth import (
    OAuthError,
    ProviderIdentity,
    configured_providers,
    consume_login_attempt,
    create_login_attempt,
    exchange_provider_code,
    resolve_social_user,
)
from .serializers import (
    ChangePasswordSerializer,
    CustomTokenObtainPairSerializer,
    RegisterSerializer,
    UserProfileSerializer,
)

logger = logging.getLogger(__name__)
OAUTH_SESSION_KEY = 'oauth_login_attempts'
MAX_SESSION_ATTEMPTS = 5


class OAuthNoStoreMixin:
    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response['Cache-Control'] = 'no-store'
        response['Pragma'] = 'no-cache'
        response['Referrer-Policy'] = 'no-referrer'
        return response


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


def _frontend_callback_fragment(**params):
    """Keep one-time completion credentials out of requests and referrer logs."""

    parts = urlsplit(settings.OAUTH_FRONTEND_CALLBACK_URL)
    fragment = dict(parse_qsl(parts.fragment, keep_blank_values=True))
    fragment.update({key: value for key, value in params.items() if value is not None})
    return urlunsplit((parts.scheme, parts.netloc, parts.path, parts.query, urlencode(fragment)))


def _state_digest(state: str) -> str:
    return hashlib.sha256(state.encode('utf-8')).hexdigest()


def _remember_oauth_attempt(request, attempt) -> None:
    now = int(timezone.now().timestamp())
    pending = request.session.get(OAUTH_SESSION_KEY, {})
    if not isinstance(pending, dict):
        pending = {}
    valid = {
        digest: record
        for digest, record in pending.items()
        if isinstance(record, dict) and int(record.get('expires_at') or 0) > now
    }
    if len(valid) >= MAX_SESSION_ATTEMPTS:
        oldest = min(valid, key=lambda digest: int(valid[digest]['expires_at']))
        valid.pop(oldest, None)
    valid[attempt.state_digest] = {
        'attempt_id': attempt.id,
        'provider': attempt.provider,
        'expires_at': int(attempt.expires_at.timestamp()),
    }
    request.session[OAUTH_SESSION_KEY] = valid


def _session_attempt_id(request, provider: str, state: str) -> int | None:
    pending = request.session.get(OAUTH_SESSION_KEY, {})
    if not isinstance(pending, dict):
        return None
    record = pending.get(_state_digest(state))
    if not isinstance(record, dict):
        return None
    if record.get('provider') != provider:
        return None
    try:
        if int(record.get('expires_at') or 0) <= int(timezone.now().timestamp()):
            return None
        return int(record['attempt_id'])
    except (KeyError, TypeError, ValueError):
        return None


def _forget_oauth_attempt(request, state: str) -> None:
    pending = request.session.get(OAUTH_SESSION_KEY, {})
    if not isinstance(pending, dict):
        return
    pending.pop(_state_digest(state), None)
    if pending:
        request.session[OAUTH_SESSION_KEY] = pending
    else:
        request.session.pop(OAUTH_SESSION_KEY, None)


def _clear_attempt_secrets(attempt) -> None:
    attempt.code_verifier = ''
    attempt.nonce = ''
    attempt.save(update_fields=('code_verifier', 'nonce'))


def _oauth_error_url(exc: OAuthError, attempt=None) -> str:
    params = {'error': exc.code, 'message': exc.message}
    if attempt is not None:
        params['next'] = attempt.next_path
        if attempt.linking_user_id:
            params['flow'] = 'link'
    return _frontend_callback(**params)


class OAuthProvidersView(OAuthNoStoreMixin, generics.GenericAPIView):
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


class OAuthStartView(OAuthNoStoreMixin, generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth_oauth_start'

    def get(self, request, provider):
        try:
            attempt, _, authorization_url = create_login_attempt(
                provider,
                next_path=request.query_params.get('next', '/profile'),
            )
            _remember_oauth_attempt(request, attempt)
        except OAuthError as exc:
            return redirect(_frontend_callback(error=exc.code, message=exc.message))
        return redirect(authorization_url)


class OAuthLinkStartView(OAuthNoStoreMixin, generics.GenericAPIView):
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


class OAuthCallbackView(OAuthNoStoreMixin, generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth_oauth_callback'

    def get(self, request, provider):
        state = str(request.query_params.get('state') or '')
        attempt = None
        try:
            attempt = consume_login_attempt(
                provider,
                state,
                anonymous_attempt_id=_session_attempt_id(request, provider, state),
            )
            if attempt.linking_user_id is None:
                _forget_oauth_attempt(request, state)
            try:
                if request.query_params.get('error'):
                    raise OAuthError('cancelled', 'Sign-in was cancelled.')
                identity = exchange_provider_code(
                    provider,
                    request.query_params.get('code', ''),
                    attempt,
                )
            finally:
                _clear_attempt_secrets(attempt)
            if attempt.linking_user_id:
                raw_link_code = secrets.token_urlsafe(48)
                OAuthLinkExchangeCode.objects.create(
                    linking_user=attempt.linking_user,
                    provider=provider,
                    issuer=identity.issuer,
                    subject=identity.subject,
                    email=identity.email,
                    email_verified=identity.email_verified,
                    token_digest=_state_digest(raw_link_code),
                    expires_at=timezone.now()
                    + timedelta(seconds=settings.OAUTH_EXCHANGE_TTL_SECONDS),
                )
                return redirect(
                    _frontend_callback_fragment(
                        link_code=raw_link_code,
                        provider=provider,
                        next=attempt.next_path,
                    )
                )
            user = resolve_social_user(provider, identity)
            raw_code = secrets.token_urlsafe(48)
            OAuthExchangeCode.objects.create(
                user=user,
                token_digest=_state_digest(raw_code),
                expires_at=timezone.now() + timedelta(seconds=settings.OAUTH_EXCHANGE_TTL_SECONDS),
            )
            return redirect(_frontend_callback_fragment(code=raw_code, next=attempt.next_path))
        except OAuthError as exc:
            return redirect(_oauth_error_url(exc, attempt))
        except Exception:
            logger.exception('Unexpected OAuth callback failure for provider=%s', provider)
            return redirect(
                _oauth_error_url(
                    OAuthError(
                        'oauth_failed',
                        'Sign-in could not be completed. Please try again.',
                    ),
                    attempt,
                )
            )


class OAuthExchangeView(OAuthNoStoreMixin, generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth_oauth_exchange'

    @transaction.atomic
    def post(self, request):
        raw_code = str(request.data.get('code') or '')
        digest = _state_digest(raw_code)
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
        if not exchange.user.is_active:
            return Response(
                {'code': 'account_inactive', 'detail': 'This account is not available.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        refresh = RefreshToken.for_user(exchange.user)
        return Response(
            {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserProfileSerializer(exchange.user).data,
            }
        )


class OAuthLinkExchangeView(OAuthNoStoreMixin, generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth_oauth_exchange'

    @transaction.atomic
    def post(self, request):
        raw_code = str(request.data.get('code') or '')
        exchange = (
            OAuthLinkExchangeCode.objects.select_for_update()
            .select_related('linking_user')
            .filter(token_digest=_state_digest(raw_code))
            .first()
        )
        if (
            not raw_code
            or exchange is None
            or exchange.used_at is not None
            or exchange.expires_at <= timezone.now()
        ):
            return Response(
                {
                    'code': 'invalid_link_exchange',
                    'detail': 'This account-link code is invalid or expired.',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if exchange.linking_user_id != request.user.id:
            return Response(
                {
                    'code': 'link_user_mismatch',
                    'detail': 'This account-link request belongs to another user.',
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        exchange.used_at = timezone.now()
        exchange.save(update_fields=('used_at',))
        if not request.user.is_active:
            return Response(
                {'code': 'account_inactive', 'detail': 'This account is not available.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        identity = ProviderIdentity(
            issuer=exchange.issuer,
            subject=exchange.subject,
            email=exchange.email,
            email_verified=exchange.email_verified,
        )
        try:
            user = resolve_social_user(
                exchange.provider,
                identity,
                linking_user=request.user,
            )
        except OAuthError as exc:
            return Response(
                {'code': exc.code, 'detail': exc.message},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({'user': UserProfileSerializer(user).data})
