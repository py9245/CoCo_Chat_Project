from django.urls import path

from randomchat.views import (
    RandomChatMatchView,
    RandomChatMessageView,
    RandomChatQueueView,
    RandomChatStateView,
)

app_name = "randomchat"

urlpatterns = [
    path("state", RandomChatStateView.as_view(), name="state"),
    path("queue", RandomChatQueueView.as_view(), name="queue"),
    path("match", RandomChatMatchView.as_view(), name="match"),
    path("messages", RandomChatMessageView.as_view(), name="messages"),
]
