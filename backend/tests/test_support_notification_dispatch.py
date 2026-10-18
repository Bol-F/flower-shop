"""A support message is durable even when optional notification delivery fails."""

from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

from celery import Celery
from django.db import transaction
from django.urls import reverse
import pytest
from rest_framework.test import APIClient

from apps.contact.models import UserMessage
from apps.contact import views
from apps.users.models import User


@pytest.fixture
def sender(db):
    return User.objects.create_user('sender', 'sender@example.test', 'test-only-password')


@pytest.fixture
def client(sender):
    client = APIClient()
    client.force_authenticate(sender)
    return client


@pytest.fixture
def notification_actions(monkeypatch):
    adapters = MagicMock(name='notification_adapters')
    publish = MagicMock(name='admin_publish')
    monkeypatch.setattr(views, 'notify_support_message_created', adapters)
    monkeypatch.setattr(views, '_publish_admin_notification', publish)
    return adapters, publish


def send(client):
    return client.post(
        reverse('contact-send'),
        {'subject': 'Synthetic support request', 'body': 'Test-only message, no real recipient.'},
        format='json',
    )


@pytest.mark.django_db
def test_support_notifications_wait_for_commit(
    client, notification_actions, django_capture_on_commit_callbacks
):
    adapters, publish = notification_actions
    with django_capture_on_commit_callbacks(execute=True) as callbacks:
        response = send(client)
        assert response.status_code == 201
        assert UserMessage.objects.count() == 1
        adapters.assert_not_called()
        publish.assert_not_called()

    assert len(callbacks) == 1
    message = UserMessage.objects.get()
    adapters.assert_called_once_with(message)
    publish.assert_called_once_with(message)


@pytest.mark.django_db
def test_rolled_back_support_message_does_not_notify(
    client, notification_actions, django_capture_on_commit_callbacks
):
    with django_capture_on_commit_callbacks(execute=True) as callbacks:
        with pytest.raises(RuntimeError, match='synthetic rollback'):
            with transaction.atomic():
                assert send(client).status_code == 201
                raise RuntimeError('synthetic rollback')

    assert UserMessage.objects.count() == 0
    assert callbacks == []
    for action in notification_actions:
        action.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize('failed_action', [0, 1])
def test_optional_delivery_failure_preserves_success_and_other_action(
    client, notification_actions, django_capture_on_commit_callbacks, failed_action, caplog
):
    notification_actions[failed_action].side_effect = RuntimeError(
        'redis://username:credential-must-not-leak@example.invalid:6379/0'
    )
    with django_capture_on_commit_callbacks(execute=True):
        response = send(client)

    assert response.status_code == 201
    assert UserMessage.objects.count() == 1
    for action in notification_actions:
        action.assert_called_once()
    assert 'saved;' in caplog.text
    assert 'credential-must-not-leak' not in caplog.text


def fake_message():
    return SimpleNamespace(
        pk=123, user=SimpleNamespace(email='synthetic@example.test'), subject='Probe'
    )


def test_notification_publish_uses_expiring_no_retry_message_and_bounded_connection(monkeypatch):
    task = MagicMock()
    task.app.conf.task_always_eager = False
    connection = task.app.connection_for_write.return_value.__enter__.return_value
    monkeypatch.setattr(views, 'notify_admin_new_message', task)

    views._publish_admin_notification(fake_message())

    task.app.connection_for_write.assert_called_once_with(
        connect_timeout=1,
        transport_options={
            'socket_connect_timeout': 1,
            'socket_timeout': 1,
            'retry_on_timeout': False,
        },
    )
    connection.ensure_connection.assert_called_once_with(max_retries=0)
    task.apply_async.assert_called_once_with(
        args=(123, 'synthetic@example.test', 'Probe'),
        connection=connection,
        retry=False,
        expires=60,
        ignore_result=True,
    )


def test_eager_local_test_mode_does_not_open_a_broker_connection(monkeypatch):
    task = MagicMock()
    task.app.conf.task_always_eager = True
    monkeypatch.setattr(views, 'notify_admin_new_message', task)

    views._publish_admin_notification(fake_message())

    task.app.connection_for_write.assert_not_called()
    task.apply_async.assert_called_once_with(
        args=(123, 'synthetic@example.test', 'Probe'),
        retry=False,
        expires=60,
        ignore_result=True,
    )


def test_unavailable_broker_is_not_retried_or_published(monkeypatch):
    task = MagicMock()
    task.app.conf.task_always_eager = False
    connection = task.app.connection_for_write.return_value.__enter__.return_value
    connection.ensure_connection.side_effect = ConnectionError('synthetic offline broker')
    monkeypatch.setattr(views, 'notify_admin_new_message', task)

    with pytest.raises(ConnectionError):
        views._publish_admin_notification(fake_message())

    connection.ensure_connection.assert_called_once_with(max_retries=0)
    task.apply_async.assert_not_called()


def test_publish_options_work_with_real_celery_producer_without_executing_task(monkeypatch):
    queue_name = f'synthetic-support-{uuid4().hex}'
    app = Celery(
        'synthetic-support', broker='memory://', backend='cache+memory://', set_as_current=False
    )
    app.conf.update(task_default_queue=queue_name, task_serializer='json', accept_content=['json'])

    @app.task(name=queue_name)
    def synthetic_task(*args):
        raise AssertionError('This test must only publish, never execute a notification task.')

    monkeypatch.setattr(views, 'notify_admin_new_message', synthetic_task)
    try:
        views._publish_admin_notification(fake_message())
        with app.connection_for_read() as connection:
            channel = connection.channel()
            queue = connection.SimpleQueue(queue_name, channel=channel)
            try:
                message = queue.get(block=False)
                assert message.headers['task'] == queue_name
                assert message.headers['ignore_result'] is True
                assert message.headers['expires']
                assert message.payload[0] == [123, 'synthetic@example.test', 'Probe']
                message.ack()
            finally:
                queue.close()
                channel.queue_delete(queue_name)
    finally:
        app.close()
