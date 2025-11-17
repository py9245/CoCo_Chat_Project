from django.urls import path

from chatrooms.consumers import ChatRoomConsumer

websocket_urlpatterns = [
    path("ws/chatrooms/<int:room_id>/", ChatRoomConsumer.as_asgi()),
]
