from channels.generic.websocket import AsyncWebsocketConsumer
import json
from channels.db import database_sync_to_async
from Tasks.models import Task
from Interactions.models import Message
from Accounts.models import CustomUser

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.task_id = self.scope['url_route']['kwargs']['task_id']
        self.room_group_name = f'chat_{self.task_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        print("data",data)
        message = data['message']
        print("message",message)
        sender = self.scope['user']
        print("sender",sender)

        # Save message to database
        await self.save_message(sender, self.task_id, message)

         # Save message to database
        # Message.objects.create(task_id=self.task_id, sender=sender, content=message)

        # Broadcast message
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender_username': sender.username
            }
        )

    async def chat_message(self, event):
        message = event['message']
        sender_username = event['sender_username']

        await self.send(text_data=json.dumps({
            'message': message,
            'sender': sender_username
        }))

    @database_sync_to_async
    def save_message(self, sender, task_id, message):
        Message.objects.create(sender=sender, task_id=task_id, content=message)


class NotesConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.task_id = self.scope['url_route']['kwargs']['task_id']
        self.user = self.scope['user']
        self.room_group_name = f'notes_{self.task_id}_{self.user.id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        content = data['content']

        # Save the note to the database
        note, created = UserNotes.objects.get_or_create(
            task_id=self.task_id,
            user=self.user
        )
        note.content = content
        note.save()

        # Broadcast the updated note to the group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'note_update',
                'content': content
            }
        )

    async def note_update(self, event):
        content = event['content']

        await self.send(text_data=json.dumps({
            'content': content
        }))