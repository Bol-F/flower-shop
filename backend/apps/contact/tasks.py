import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def notify_admin_new_message(message_id, user_email, subject):
    """Push real-time WebSocket notification to all connected admin clients."""
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync

    channel_layer = get_channel_layer()
    if channel_layer is None:
        logger.warning('Channel layer not configured — skipping WebSocket notification.')
        return

    async_to_sync(channel_layer.group_send)(
        'admin_notifications',
        {
            'type': 'new_message',
            'message_id': message_id,
            'user': user_email,
            'subject': subject,
        },
    )
    logger.info('Admin notified of new message #%s from %s', message_id, user_email)


@shared_task
def unread_messages_daily_summary():
    """Periodic task (Celery Beat): logs count of unread inbox messages."""
    from apps.contact.models import UserMessage

    count = UserMessage.objects.filter(is_read=False).count()
    logger.info('Daily summary: %d unread message(s) in admin inbox.', count)
    return count
