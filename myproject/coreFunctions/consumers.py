from django.utils.timesince import timesince
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from channels.generic.websocket import AsyncWebsocketConsumer
import json
import datetime

from authUser.models import User
from coreFunctions.models import ChatMessage

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get('message')
        sender_username = data.get('sender')
        timestamp = data.get('timestamp', datetime.datetime.now().isoformat())
        
        try:
            # Get sender and receiver user objects
            sender = User.objects.get(username=sender_username)
            receiver = User.objects.get(username=data['receiver'])
            
            # Create and save the chat message
            chat_message = ChatMessage(
                user=sender,  # Set user as sender 
                sender=sender,
                receiver=receiver,
                message=message,
            )
            chat_message.save()
            
            print(f"Message saved to database: {sender_username} to {receiver.username}: {message}")
            
            # Send to the chat room
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'sender': sender_username,
                    'receiver': receiver.username,
                    'timestamp': timestamp,
                }
            )
            
            # Also send notification to receiver's notification group
            async_to_sync(self.channel_layer.group_send)(
                f'notifications_{receiver.username}',
                {
                    'type': 'send_notification',
                    'message': message,
                    'sender': sender_username,
                    'timestamp': timestamp,
                }
            )
            
        except User.DoesNotExist as e:
            print(f"Error: User not found - {e}")
        except Exception as e:
            print(f"Error saving message: {e}")

    def chat_message(self, event):
        self.send(text_data=json.dumps(event))

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.username = self.scope['url_route']['kwargs']['username']
        self.room_group_name = f'notifications_{self.username}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def send_notification(self, event):
        # Send notification to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'new_message',  
            'message': event['message'],
            'sender': event.get('sender'),
            'timestamp': event.get('timestamp'),
        }))