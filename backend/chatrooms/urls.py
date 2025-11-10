from django.urls import path

from chatrooms.views import ChatMessageListCreateView


app_name = "chatrooms"

urlpatterns = [
    path("messages", ChatMessageListCreateView.as_view(), name="message-list"),
]
