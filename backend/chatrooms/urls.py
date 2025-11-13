from django.urls import path

from chatrooms.views import (
    ChatRoomJoinView,
    ChatRoomLeaveView,
    ChatRoomListCreateView,
    ChatRoomMessageListCreateView,
    RandomChatMatchView,
    RandomChatMessageView,
    RandomChatQueueView,
    RandomChatStateView,
)


app_name = "chatrooms"

urlpatterns = [
    path("rooms", ChatRoomListCreateView.as_view(), name="room-list"),
    path("rooms/join", ChatRoomJoinView.as_view(), name="room-join"),
    path("rooms/<int:room_id>/leave", ChatRoomLeaveView.as_view(), name="room-leave"),
    path("rooms/<int:room_id>/messages", ChatRoomMessageListCreateView.as_view(), name="room-messages"),
    path("random/state", RandomChatStateView.as_view(), name="random-state"),
    path("random/queue", RandomChatQueueView.as_view(), name="random-queue"),
    path("random/match", RandomChatMatchView.as_view(), name="random-match"),
    path("random/messages", RandomChatMessageView.as_view(), name="random-messages"),
]
