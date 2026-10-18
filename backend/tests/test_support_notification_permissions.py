"""WebSocket notifications expose customer identities only to support readers."""

from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import AnonymousUser, Permission
from django.test import override_settings
import pytest

from apps.contact.consumers import AdminNotificationConsumer
from apps.users.models import User


IN_MEMORY_CHANNEL_LAYER = {'default': {'BACKEND': 'channels.layers.InMemoryChannelLayer'}}
EVENT = {
    'type': 'new_message',
    'message_id': 7,
    'user': 'private-customer@example.test',
    'subject': 'A private support question',
}


def make_user(role):
    if role == 'anonymous':
        return AnonymousUser()
    user = User.objects.create_user(
        role,
        f'{role}@example.test',
        'password',
        is_staff=role != 'customer',
        is_active=role != 'inactive',
        is_superuser=role == 'superuser',
    )
    if role in ('reader', 'customer', 'inactive'):
        user.user_permissions.add(
            Permission.objects.get(content_type__app_label='contact', codename='view_usermessage')
        )
    return user


def communicator_for(user):
    communicator = WebsocketCommunicator(
        AdminNotificationConsumer.as_asgi(), '/ws/admin/notifications/'
    )
    communicator.scope['user'] = user
    return communicator


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize('role', ['anonymous', 'staff', 'customer', 'inactive'])
@override_settings(CHANNEL_LAYERS=IN_MEMORY_CHANNEL_LAYER)
def test_support_websocket_denies_unprivileged_connections(role):
    user = make_user(role)

    async def scenario():
        communicator = communicator_for(user)
        connected, code = await communicator.connect()
        assert connected is False
        assert code == 4403
        await communicator.disconnect()

    async_to_sync(scenario)()


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize('role', ['reader', 'superuser'])
@override_settings(CHANNEL_LAYERS=IN_MEMORY_CHANNEL_LAYER)
def test_support_websocket_accepts_permissioned_readers(role):
    user = make_user(role)

    async def scenario():
        communicator = communicator_for(user)
        connected, _ = await communicator.connect()
        assert connected is True
        await get_channel_layer().group_send(AdminNotificationConsumer.GROUP_NAME, EVENT)
        assert await communicator.receive_json_from() == EVENT
        await communicator.disconnect()

    async_to_sync(scenario)()


@pytest.mark.django_db(transaction=True)
@override_settings(CHANNEL_LAYERS=IN_MEMORY_CHANNEL_LAYER)
def test_permission_revocation_stops_notifications_on_existing_socket():
    user = make_user('reader')
    # Even a user whose original Django permission cache was populated is rechecked.
    assert user.has_perm('contact.view_usermessage')

    async def scenario():
        communicator = communicator_for(user)
        connected, _ = await communicator.connect()
        assert connected is True
        await database_sync_to_async(user.user_permissions.clear)()
        await get_channel_layer().group_send(AdminNotificationConsumer.GROUP_NAME, EVENT)
        assert await communicator.receive_output() == {'type': 'websocket.close', 'code': 4403}
        await communicator.disconnect()

    async_to_sync(scenario)()
