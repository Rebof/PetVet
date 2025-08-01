from django.urls import re_path
from coreFunctions import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<room_name>[\w-]+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/notifications/(?P<username>\w+)/$', consumers.NotificationConsumer.as_asgi()),


]