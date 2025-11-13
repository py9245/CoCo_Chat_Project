from django.urls import path

from chatrooms.views import (
    ChatRoomJoinView,
    ChatRoomLeaveView,
    ChatRoomListCreateView,
    ChatRoomMessageListCreateView,
)


app_name = "chatrooms"

urlpatterns = [
    path("rooms", ChatRoomListCreateView.as_view(), name="room-list"),
    path("rooms/join", ChatRoomJoinView.as_view(), name="room-join"),
    path("rooms/<int:room_id>/leave", ChatRoomLeaveView.as_view(), name="room-leave"),
    path("rooms/<int:room_id>/messages", ChatRoomMessageListCreateView.as_view(), name="room-messages"),
]
