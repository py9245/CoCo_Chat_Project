from django.conf import settings
from django.db import models


class ChatMessage(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chatroom_messages",
    )
    content = models.TextField()
    is_anonymous = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.display_name}: {self.content[:30]}"

    @property
    def display_name(self):
        if self.is_anonymous:
            return "익명"
        return self.user.username
