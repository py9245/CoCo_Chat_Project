from django.conf import settings
from django.db import models


class Message(models.Model):
    """Simple piece of content rendered by the Vue frontend."""

    title = models.CharField(max_length=120)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.title}"


class ChatMessage(models.Model):
    """Realtime-style 자유 채팅방 메시지."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_messages",
    )
    content = models.TextField()
    is_anonymous = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"ChatMessage({self.display_name}): {self.content[:30]}"

    @property
    def display_name(self) -> str:
        if self.is_anonymous:
            return "익명"
        if self.user_id:
            return self.user.username
        return "알 수 없음"
