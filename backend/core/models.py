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
