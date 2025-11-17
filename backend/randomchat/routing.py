from django.urls import path

from randomchat.consumers import RandomChatConsumer


websocket_urlpatterns = [
    path("ws/random-chat/", RandomChatConsumer.as_asgi()),
]
