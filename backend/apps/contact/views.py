from django.utils import timezone
from rest_framework import generics, permissions

from apps.common.permissions import IsCustomer
from .models import UserMessage
from .serializers import (
    UserMessageCreateSerializer,
    UserMessageOwnSerializer,
    UserMessageAdminSerializer,
)
from .tasks import notify_admin_new_message


class SendMessageView(generics.CreateAPIView):
    """Customers send a message to support; staff answer from the dashboard."""
    serializer_class = UserMessageCreateSerializer
    permission_classes = [IsCustomer]

    def perform_create(self, serializer):
        msg = serializer.save(user=self.request.user)
        try:
            notify_admin_new_message.delay(msg.id, self.request.user.email, msg.subject)
        except Exception:
            pass  # Don't break the request if Redis / Celery is down


class MyMessagesView(generics.ListAPIView):
    """Authenticated users see their own messages and any admin replies."""
    serializer_class = UserMessageOwnSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserMessage.objects.filter(user=self.request.user)


class AdminMessageListView(generics.ListAPIView):
    """Admin: list all incoming messages ordered newest first."""
    serializer_class = UserMessageAdminSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = UserMessage.objects.select_related('user').all()


class AdminMessageDetailView(generics.RetrieveUpdateAPIView):
    """Admin: read a message; PATCH to mark read or add a reply."""
    serializer_class = UserMessageAdminSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = UserMessage.objects.select_related('user').all()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.is_read:
            instance.is_read = True
            instance.save(update_fields=['is_read'])
        return super().retrieve(request, *args, **kwargs)

    def perform_update(self, serializer):
        extra = {}
        if serializer.validated_data.get('admin_reply'):
            extra['replied_at'] = timezone.now()
            extra['is_read'] = True
        serializer.save(**extra)
