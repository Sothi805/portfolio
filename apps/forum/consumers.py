from channels.generic.websocket import AsyncWebsocketConsumer
import json


class NotificationConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time notifications"""

    async def connect(self):
        if self.scope['user'].is_anonymous:
            await self.close()
            return
        self.user_id = self.scope['user'].id
        self.group_name = f'user_{self.user_id}_notifications'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def notification_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'title': event.get('title'),
            'message': event.get('message'),
            'notification_id': event.get('notification_id'),
        }))


class ForumConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time forum thread updates"""

    async def connect(self):
        self.thread_id = self.scope['url_route']['kwargs']['thread_id']
        self.group_name = f'thread_{self.thread_id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data.get('type') == 'new_reply':
            from django.utils.timezone import now
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'reply_posted',
                    'user': data.get('user'),
                    'content': data.get('content'),
                    'timestamp': str(now()),
                }
            )

    async def reply_posted(self, event):
        await self.send(text_data=json.dumps({
            'type': 'reply_posted',
            'user': event['user'],
            'content': event['content'],
            'timestamp': event['timestamp'],
        }))
