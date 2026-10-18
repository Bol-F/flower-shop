import json
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model

from apps.common.permissions import staff_has_model_permissions


@database_sync_to_async
def can_receive_support_notifications(user):
    if not user or not user.is_authenticated:
        return False
    # Fetch current permissions instead of reusing the connection's cached user.
    current_user = get_user_model().objects.filter(pk=user.pk).first()
    return staff_has_model_permissions(current_user, 'contact.view_usermessage')


class AdminNotificationConsumer(AsyncWebsocketConsumer):
    GROUP_NAME = 'admin_notifications'

    async def connect(self):
        user = self.scope.get('user')
        if not await can_receive_support_notifications(user):
            await self.close(code=4403)
            return
        await self.channel_layer.group_add(self.GROUP_NAME, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.GROUP_NAME, self.channel_name)

    # Handler called by notify_admin_new_message task
    async def new_message(self, event):
        if not await can_receive_support_notifications(self.scope.get('user')):
            await self.channel_layer.group_discard(self.GROUP_NAME, self.channel_name)
            await self.close(code=4403)
            return
        await self.send(
            text_data=json.dumps(
                {
                    'type': 'new_message',
                    'message_id': event['message_id'],
                    'user': event['user'],
                    'subject': event['subject'],
                }
            )
        )
