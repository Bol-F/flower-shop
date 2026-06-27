import logging

from django.conf import settings

from .models import NotificationLog, Order

logger = logging.getLogger(__name__)


ORDER_STATUS_EVENTS = {
    Order.Status.CONFIRMED: NotificationLog.Event.ORDER_CONFIRMED,
    Order.Status.PREPARING: NotificationLog.Event.ORDER_PREPARING,
    Order.Status.COURIER_PICKED_UP: NotificationLog.Event.COURIER_PICKED_UP,
    Order.Status.DELIVERED: NotificationLog.Event.ORDER_DELIVERED,
}


def notify_order_created(order: Order) -> list[NotificationLog]:
    return send_order_notification(order, NotificationLog.Event.ORDER_CREATED)


def notify_order_status_changed(order: Order) -> list[NotificationLog]:
    event = ORDER_STATUS_EVENTS.get(order.status)
    if not event:
        return []
    return send_order_notification(order, event)


def notify_payment_status_changed(order: Order) -> list[NotificationLog]:
    return send_order_notification(order, NotificationLog.Event.PAYMENT_STATUS_CHANGED)


def send_order_notification(order: Order, event: str) -> list[NotificationLog]:
    message = build_notification_message(order, event)
    logs = [_log_console(order, event, message)]

    if getattr(settings, 'EMAIL_HOST_USER', ''):
        logs.append(_placeholder_log(order, event, NotificationLog.Channel.EMAIL, message))

    if (
        getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
        and getattr(settings, 'TELEGRAM_ADMIN_CHAT_ID', '')
    ):
        logs.append(_placeholder_log(order, event, NotificationLog.Channel.TELEGRAM, message))

    return logs


def build_notification_message(order: Order, event: str) -> str:
    event_label = dict(NotificationLog.Event.choices).get(event, event)
    return (
        f'{event_label}: Order #{order.id} '
        f'({order.get_status_display()}, payment {order.get_payment_status_display()}) '
        f'total {order.total_price}'
    )


def _log_console(order: Order, event: str, message: str) -> NotificationLog:
    logger.info(message)
    return NotificationLog.objects.create(
        order=order,
        event=event,
        channel=NotificationLog.Channel.CONSOLE,
        status=NotificationLog.Status.SUCCESS,
        message=message,
    )


def _placeholder_log(
    order: Order,
    event: str,
    channel: str,
    message: str,
) -> NotificationLog:
    return NotificationLog.objects.create(
        order=order,
        event=event,
        channel=channel,
        status=NotificationLog.Status.SKIPPED,
        message=message,
        error='Provider integration is not configured yet.',
    )
