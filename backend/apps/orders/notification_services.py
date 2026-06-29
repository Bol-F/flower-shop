import logging
import re
from dataclasses import dataclass

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
import requests

from .models import NotificationLog, Order

logger = logging.getLogger(__name__)
TELEGRAM_API_TIMEOUT_SECONDS = 5


ORDER_STATUS_EVENTS = {
    Order.Status.CONFIRMED: NotificationLog.Event.ORDER_CONFIRMED,
    Order.Status.PREPARING: NotificationLog.Event.ORDER_PREPARING,
    Order.Status.COURIER_PICKED_UP: NotificationLog.Event.COURIER_PICKED_UP,
    Order.Status.DELIVERED: NotificationLog.Event.ORDER_DELIVERED,
}
TELEGRAM_EVENT_TYPES = {
    NotificationLog.Event.ORDER_CREATED,
    NotificationLog.Event.ORDER_CONFIRMED,
    NotificationLog.Event.COURIER_PICKED_UP,
    NotificationLog.Event.ORDER_DELIVERED,
    NotificationLog.Event.PAYMENT_PAID,
    NotificationLog.Event.PAYMENT_FAILED,
    NotificationLog.Event.SUPPORT_MESSAGE_CREATED,
}
EMAIL_EVENT_TYPES = {
    NotificationLog.Event.ORDER_CREATED,
    NotificationLog.Event.ORDER_CONFIRMED,
    NotificationLog.Event.ORDER_PREPARING,
    NotificationLog.Event.COURIER_PICKED_UP,
    NotificationLog.Event.ORDER_DELIVERED,
    NotificationLog.Event.PAYMENT_PAID,
    NotificationLog.Event.PAYMENT_FAILED,
}


@dataclass(frozen=True)
class NotificationPayload:
    event_type: str
    recipient: str
    subject: str
    message: str
    related_order: Order | None = None


def notify_order_created(order: Order) -> list[NotificationLog]:
    return send_notification(
        NotificationPayload(
            event_type=NotificationLog.Event.ORDER_CREATED,
            recipient=_order_recipient(order),
            subject=f'Order #{order.id} created',
            message=_order_message(order, NotificationLog.Event.ORDER_CREATED),
            related_order=order,
        )
    )


def notify_order_status_changed(order: Order) -> list[NotificationLog]:
    event_type = ORDER_STATUS_EVENTS.get(order.status)
    if not event_type:
        return []
    return send_notification(
        NotificationPayload(
            event_type=event_type,
            recipient=_order_recipient(order),
            subject=f'Order #{order.id} {order.get_status_display()}',
            message=_order_message(order, event_type),
            related_order=order,
        )
    )


def notify_payment_status_changed(order: Order) -> list[NotificationLog]:
    event_type = _payment_event_type(order)
    if not event_type:
        return []
    return send_notification(
        NotificationPayload(
            event_type=event_type,
            recipient=_order_recipient(order),
            subject=f'Order #{order.id} payment {order.get_payment_status_display()}',
            message=_order_message(order, event_type),
            related_order=order,
        )
    )


def notify_support_message_created(message) -> list[NotificationLog]:
    user_email = getattr(getattr(message, 'user', None), 'email', '')
    subject = getattr(message, 'subject', '') or 'Support message'
    body = getattr(message, 'body', '')
    return send_notification(
        NotificationPayload(
            event_type=NotificationLog.Event.SUPPORT_MESSAGE_CREATED,
            recipient=_support_recipient(),
            subject=f'New support message: {subject}',
            message=f'New support message from {user_email or "customer"}: {body}',
        )
    )


def send_notification(payload: NotificationPayload) -> list[NotificationLog]:
    if not getattr(settings, 'NOTIFICATIONS_ENABLED', True):
        return [
            _create_log(
                payload,
                NotificationLog.Channel.CONSOLE,
                NotificationLog.Status.SKIPPED,
                error_message='Notifications are disabled by NOTIFICATIONS_ENABLED=false.',
            )
        ]

    logger.info(
        'Notification %s to %s: %s\n%s',
        payload.event_type,
        payload.recipient or 'console',
        payload.subject,
        payload.message,
    )

    logs = [
        _create_log(
            payload,
            NotificationLog.Channel.CONSOLE,
            NotificationLog.Status.SENT,
            sent_at=timezone.now(),
        )
    ]

    if _should_create_email_log(payload.event_type):
        logs.append(_send_email(payload))

    if _should_create_telegram_log(payload.event_type):
        logs.append(_send_telegram(payload))

    return logs


def _send_email(payload: NotificationPayload) -> NotificationLog:
    if not getattr(settings, 'EMAIL_NOTIFICATIONS_ENABLED', False):
        return _create_log(
            payload,
            NotificationLog.Channel.EMAIL,
            NotificationLog.Status.SKIPPED,
            error_message='Email notifications are disabled.',
        )

    recipient = _customer_email(payload)
    if not recipient:
        return _create_log(
            payload,
            NotificationLog.Channel.EMAIL,
            NotificationLog.Status.SKIPPED,
            recipient='',
            error_message='Customer email is missing.',
        )

    if not _email_configured():
        return _create_log(
            payload,
            NotificationLog.Channel.EMAIL,
            NotificationLog.Status.SKIPPED,
            recipient=recipient,
            error_message='Email notifications are enabled but email credentials are missing.',
        )

    subject = _email_subject(payload)
    message = _email_message(payload)
    sent_at = timezone.now()
    try:
        sent_count = send_mail(
            subject,
            message,
            getattr(settings, 'DEFAULT_FROM_EMAIL', ''),
            [recipient],
            fail_silently=False,
        )
    except Exception as exc:
        return _create_log(
            payload,
            NotificationLog.Channel.EMAIL,
            NotificationLog.Status.FAILED,
            recipient=recipient,
            subject=subject,
            message=message,
            error_message=str(exc),
        )

    if sent_count < 1:
        return _create_log(
            payload,
            NotificationLog.Channel.EMAIL,
            NotificationLog.Status.FAILED,
            recipient=recipient,
            subject=subject,
            message=message,
            error_message='Email backend did not send any messages.',
        )

    return _create_log(
        payload,
        NotificationLog.Channel.EMAIL,
        NotificationLog.Status.SENT,
        recipient=recipient,
        subject=subject,
        message=message,
        sent_at=sent_at,
    )


def _send_telegram(payload: NotificationPayload) -> NotificationLog:
    if not getattr(settings, 'TELEGRAM_NOTIFICATIONS_ENABLED', False):
        return _create_log(
            payload,
            NotificationLog.Channel.TELEGRAM,
            NotificationLog.Status.SKIPPED,
            recipient=_telegram_recipient(),
            error_message='Telegram notifications are disabled.',
        )

    if not _telegram_configured():
        return _create_log(
            payload,
            NotificationLog.Channel.TELEGRAM,
            NotificationLog.Status.SKIPPED,
            recipient=_telegram_recipient(),
            error_message='Telegram notifications are enabled but Telegram credentials are missing.',
        )

    sent_at = timezone.now()
    message = _telegram_message(payload)
    try:
        response = requests.post(
            _telegram_api_url(),
            json={
                'chat_id': getattr(settings, 'TELEGRAM_ADMIN_CHAT_ID', ''),
                'text': message,
                'disable_web_page_preview': True,
            },
            timeout=TELEGRAM_API_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        return _create_log(
            payload,
            NotificationLog.Channel.TELEGRAM,
            NotificationLog.Status.FAILED,
            recipient=_telegram_recipient(),
            message=message,
            error_message=_sanitize_telegram_error(str(exc)),
        )

    response_text = _safe_response_text(response)
    if response.status_code != 200:
        return _create_log(
            payload,
            NotificationLog.Channel.TELEGRAM,
            NotificationLog.Status.FAILED,
            recipient=_telegram_recipient(),
            message=message,
            error_message=(
                f'Telegram API returned HTTP {response.status_code}: {response_text}'
            ),
        )

    try:
        data = response.json()
    except ValueError:
        return _create_log(
            payload,
            NotificationLog.Channel.TELEGRAM,
            NotificationLog.Status.FAILED,
            recipient=_telegram_recipient(),
            message=message,
            error_message='Telegram API returned invalid JSON.',
        )

    if not data.get('ok'):
        description = str(data.get('description') or 'Telegram API returned ok=false.')
        return _create_log(
            payload,
            NotificationLog.Channel.TELEGRAM,
            NotificationLog.Status.FAILED,
            recipient=_telegram_recipient(),
            message=message,
            error_message=_sanitize_telegram_error(description),
        )

    return _create_log(
        payload,
        NotificationLog.Channel.TELEGRAM,
        NotificationLog.Status.SENT,
        recipient=_telegram_recipient(),
        message=message,
        sent_at=sent_at,
    )


def _create_log(
    payload: NotificationPayload,
    channel: str,
    status: str,
    *,
    recipient: str | None = None,
    subject: str = '',
    message: str = '',
    error_message: str = '',
    sent_at=None,
) -> NotificationLog:
    return NotificationLog.objects.create(
        event_type=payload.event_type,
        channel=channel,
        recipient=payload.recipient if recipient is None else recipient,
        subject=subject or payload.subject,
        message=message or payload.message,
        status=status,
        error_message=error_message,
        related_order=payload.related_order,
        sent_at=sent_at,
    )


def _order_recipient(order: Order) -> str:
    return getattr(order.user, 'email', '') or getattr(order.user, 'username', '')


def _support_recipient() -> str:
    return (
        getattr(settings, 'TELEGRAM_ADMIN_CHAT_ID', '')
        or getattr(settings, 'EMAIL_HOST_USER', '')
        or 'support-admin'
    )


def _order_message(order: Order, event_type: str) -> str:
    if event_type == NotificationLog.Event.ORDER_CREATED:
        return _new_order_message(order)

    event_label = dict(NotificationLog.Event.choices).get(event_type, event_type)
    return (
        f'{event_label}: Order #{order.id} '
        f'({order.get_status_display()}, payment {order.get_payment_status_display()}) '
        f'total {order.total_price}'
    )


def _new_order_message(order: Order) -> str:
    lines = [
        f'New order #{order.id}',
        '',
        f'Customer: {_customer_label(order)}',
        f'Recipient: {order.recipient_name or "Not provided"}',
        f'Phone: {order.recipient_phone or order.phone}',
        f'Address: {order.delivery_address or order.shipping_address}',
        f'Delivery: {_delivery_label(order)}',
        f'Payment: {order.payment_method} / {order.payment_status}',
        f'Status: {order.status}',
        f'Delivery fee: {order.delivery_fee} {_order_currency(order)}',
        f'Total: {order.total_price} {_order_currency(order)}',
    ]
    if order.delivery_zone:
        lines.insert(7, f'Zone: {order.delivery_zone.name}')
    if order.gift_note:
        lines.append(f'Gift note: {order.gift_note}')
    return '\n'.join(lines)


def _telegram_message(payload: NotificationPayload) -> str:
    if payload.event_type == NotificationLog.Event.SUPPORT_MESSAGE_CREATED:
        return payload.message
    return payload.message


def _payment_event_type(order: Order) -> str:
    if order.payment_status == Order.PaymentStatus.PAID:
        return NotificationLog.Event.PAYMENT_PAID
    if order.payment_status == Order.PaymentStatus.FAILED:
        return NotificationLog.Event.PAYMENT_FAILED
    return ''


def _email_subject(payload: NotificationPayload) -> str:
    order = payload.related_order
    if not order:
        return payload.subject

    subject_by_event = {
        NotificationLog.Event.ORDER_CREATED: f'Bloom & Petal: Your order #{order.id} was created',
        NotificationLog.Event.ORDER_CONFIRMED: f'Bloom & Petal: Your order #{order.id} is confirmed',
        NotificationLog.Event.ORDER_PREPARING: f'Bloom & Petal: Your order #{order.id} is being prepared',
        NotificationLog.Event.COURIER_PICKED_UP: f'Bloom & Petal: Your order #{order.id} is on the way',
        NotificationLog.Event.ORDER_DELIVERED: f'Bloom & Petal: Your order #{order.id} was delivered',
        NotificationLog.Event.PAYMENT_PAID: f'Bloom & Petal: Payment received for order #{order.id}',
        NotificationLog.Event.PAYMENT_FAILED: f'Bloom & Petal: Payment failed for order #{order.id}',
    }
    return subject_by_event.get(payload.event_type, payload.subject)


def _email_message(payload: NotificationPayload) -> str:
    order = payload.related_order
    if not order:
        return payload.message

    friendly_message_by_event = {
        NotificationLog.Event.ORDER_CREATED: 'Thanks for your order. We received it and will start reviewing the delivery details.',
        NotificationLog.Event.ORDER_CONFIRMED: 'Your order has been confirmed by our team.',
        NotificationLog.Event.ORDER_PREPARING: 'Your flowers are being prepared.',
        NotificationLog.Event.COURIER_PICKED_UP: 'Your order has been picked up by the courier and is on the way.',
        NotificationLog.Event.ORDER_DELIVERED: 'Your order has been delivered. Thank you for choosing Bloom & Petal.',
        NotificationLog.Event.PAYMENT_PAID: 'We received your payment.',
        NotificationLog.Event.PAYMENT_FAILED: 'Your payment was not completed. Please contact support or choose another payment option.',
    }
    lines = [
        friendly_message_by_event.get(payload.event_type, 'Your order has been updated.'),
        '',
        f'Order: #{order.id}',
        f'Order status: {order.get_status_display()}',
        f'Payment status: {order.get_payment_status_display()}',
        f'Delivery address: {order.delivery_address or order.shipping_address}',
        f'Delivery: {_delivery_label(order)}',
        f'Recipient: {order.recipient_name or "Not provided"}',
        f'Total: {order.total_price} {_order_currency(order)}',
        '',
        'Bloom & Petal',
    ]
    return '\n'.join(lines)


def _customer_email(payload: NotificationPayload) -> str:
    order = payload.related_order
    if not order:
        return payload.recipient
    return getattr(order.user, 'email', '') or ''


def _email_configured() -> bool:
    return bool(
        getattr(settings, 'EMAIL_HOST', '')
        and getattr(settings, 'EMAIL_HOST_USER', '')
        and getattr(settings, 'EMAIL_HOST_PASSWORD', '')
        and getattr(settings, 'DEFAULT_FROM_EMAIL', '')
    )


def _telegram_configured() -> bool:
    return bool(
        getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
        and getattr(settings, 'TELEGRAM_ADMIN_CHAT_ID', '')
    )


def _telegram_recipient() -> str:
    return getattr(settings, 'TELEGRAM_ADMIN_CHAT_ID', '') or 'telegram-admin'


def _should_create_email_log(event_type: str) -> bool:
    return event_type in EMAIL_EVENT_TYPES


def _should_create_telegram_log(event_type: str) -> bool:
    return event_type in TELEGRAM_EVENT_TYPES


def _telegram_api_url() -> str:
    return f'https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage'


def _safe_response_text(response) -> str:
    return _sanitize_telegram_error((response.text or '')[:500])


def _sanitize_telegram_error(message: str) -> str:
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
    sanitized = message.replace(token, '[redacted]') if token else message
    return re.sub(r'bot[^/\s]+', 'bot[redacted]', sanitized)


def _customer_label(order: Order) -> str:
    username = getattr(order.user, 'username', '')
    email = getattr(order.user, 'email', '')
    if username and email:
        return f'{username} <{email}>'
    return email or username or 'Customer'


def _delivery_label(order: Order) -> str:
    date = order.delivery_date.isoformat() if order.delivery_date else 'Not selected'
    slot = order.delivery_time_slot or 'Not selected'
    return f'{date}, {slot}'


def _order_currency(order: Order) -> str:
    if order.city and getattr(order.city, 'currency', ''):
        return order.city.currency
    return getattr(order.user, 'currency', '') or 'UZS'
