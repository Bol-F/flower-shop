import json
from channels.generic.websocket import AsyncWebsocketConsumer


class AdminNotificationConsumer(AsyncWebsocketConsumer):
    GROUP_NAME = 'admin_notifications'

    async def connect(self):
        user = self.scope.get('user')
        if not user or not user.is_authenticated or not user.is_staff:
            await self.close()
            return
        await self.channel_layer.group_add(self.GROUP_NAME, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.GROUP_NAME, self.channel_name)

    # Handler called by notify_admin_new_message task
    async def new_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'new_message',
            'message_id': event['message_id'],
            'user': event['user'],
            'subject': event['subject'],
        }))
