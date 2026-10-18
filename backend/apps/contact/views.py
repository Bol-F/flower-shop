import logging

from django.db import transaction
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from apps.common.permissions import (
    HasStaffModelPermissions,
    IsCustomer,
    staff_has_model_permissions,
)
from apps.orders.notifications import notify_support_message_created
from .models import UserMessage
from .serializers import (
    AdminReplyCreateSerializer,
    UserMessageCreateSerializer,
    UserMessageOwnSerializer,
    UserMessageAdminSerializer,
)
from .tasks import notify_admin_new_message


logger = logging.getLogger(__name__)
SUPPORT_BROKER_TIMEOUT_SECONDS = 1


def _publish_admin_notification(message):
    task = notify_admin_new_message
    options = {
        'args': (message.pk, message.user.email, message.subject),
        'retry': False,
        'expires': 60,
        'ignore_result': True,
    }
    if task.app.conf.task_always_eager:
        task.apply_async(**options)
        return

    # This best-effort UI hint must not hold up a saved support request while
    # Redis is unreachable. A dedicated producer bounds both connect and read
    # waits without changing worker/beat retry behavior for important jobs.
    with task.app.connection_for_write(
        connect_timeout=SUPPORT_BROKER_TIMEOUT_SECONDS,
        transport_options={
            'socket_connect_timeout': SUPPORT_BROKER_TIMEOUT_SECONDS,
            'socket_timeout': SUPPORT_BROKER_TIMEOUT_SECONDS,
            'retry_on_timeout': False,
        },
    ) as connection:
        connection.ensure_connection(max_retries=0)
        task.apply_async(connection=connection, **options)


def _notify_support_after_commit(message):
    for label, action in (
        ('notification adapters', notify_support_message_created),
        ('admin websocket publish', _publish_admin_notification),
    ):
        try:
            action(message)
        except Exception as exc:
            # Keep the durable message available in the inbox. Do not log
            # exception text, which can contain a credential-bearing broker URL.
            logger.warning(
                'Support message #%s saved; %s failed (%s).',
                message.pk,
                label,
                type(exc).__name__,
            )


class SendMessageView(generics.CreateAPIView):
    """Customers send a message to support; staff answer from the dashboard."""

    serializer_class = UserMessageCreateSerializer
    permission_classes = [IsCustomer]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'support_message'

    def perform_create(self, serializer):
        msg = serializer.save(user=self.request.user)
        transaction.on_commit(lambda: _notify_support_after_commit(msg), robust=True)


class MyMessagesView(generics.ListAPIView):
    """Authenticated users see their own messages and any admin replies."""

    serializer_class = UserMessageOwnSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserMessage.objects.filter(user=self.request.user)


class AdminMessageListView(generics.ListAPIView):
    """Admin: list all incoming messages ordered newest first."""

    serializer_class = UserMessageAdminSerializer
    permission_classes = [HasStaffModelPermissions]
    staff_permissions = ('contact.view_usermessage',)
    queryset = UserMessage.objects.select_related('user').all()


class AdminMessageDetailView(generics.RetrieveUpdateAPIView):
    """Admin: read a message; PATCH to mark read or add a reply."""

    serializer_class = UserMessageAdminSerializer
    permission_classes = [HasStaffModelPermissions]
    queryset = UserMessage.objects.select_related('user').all()

    @property
    def staff_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return ('contact.view_usermessage',)
        return ('contact.change_usermessage',)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.is_read and staff_has_model_permissions(
            request.user, 'contact.change_usermessage'
        ):
            instance.is_read = True
            instance.save(update_fields=['is_read'])
        return super().retrieve(request, *args, **kwargs)

    def perform_update(self, serializer):
        extra = {}
        if serializer.validated_data.get('admin_reply'):
            extra['replied_at'] = timezone.now()
            extra['is_read'] = True
        serializer.save(**extra)


class AdminReplyView(generics.GenericAPIView):
    """Admin: send another message into the selected customer's conversation."""

    serializer_class = AdminReplyCreateSerializer
    permission_classes = [HasStaffModelPermissions]
    staff_permissions = ('contact.change_usermessage',)
    queryset = UserMessage.objects.select_related('user').all()

    def post(self, request, *args, **kwargs):
        target = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not target.is_from_admin and not target.is_read:
            target.is_read = True
            target.save(update_fields=['is_read'])

        reply = UserMessage.objects.create(
            user=target.user,
            subject=target.subject,
            body=serializer.validated_data['body'],
            is_from_admin=True,
            is_read=True,
        )
        return Response(
            UserMessageAdminSerializer(reply).data,
            status=status.HTTP_201_CREATED,
        )
