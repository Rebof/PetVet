from django.utils.timesince import timesince

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

import json


from authUser.models import User, PetOwnerProfile, VetProfile
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
        sender = User.objects.get(username=sender_username)
        # try:
        #     sender = User.objects.get(username=sender_username)
            
        #     # Check if the sender is a Vet or Pet Owner and get their profile image
        #     if VetProfile.objects.filter(user=sender).exists():
        #         profile_image = VetProfile.objects.get(user=sender).vet_image.url
        #     elif PetOwnerProfile.objects.filter(user=sender).exists():
        #         profile_image = PetOwnerProfile.objects.get(user=sender).human_image.url
        #     else:
        #         profile_image = ''  # Default or empty if no profile found

        # except User.DoesNotExist:
        #     profile_image = ''

        receiver = User.objects.get(username=data['receiver'])
        chat_message = ChatMessage(
            sender=sender,
            receiver=receiver,
            message=message,
        )
        chat_message.save()

        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': sender_username,
                # 'profile_image': profile_image,
                'receiver': receiver.username,
            }
        )

    def chat_message(self, event):
        self.send(text_data=json.dumps(event))