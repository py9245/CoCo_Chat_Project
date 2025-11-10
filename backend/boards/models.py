import os
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


def board_attachment_upload(instance, filename):
    base, ext = os.path.splitext(filename)
    username = slugify(getattr(instance.author, "username", "") or "user")
    user_pk = instance.author_id or "anon"
    unique = uuid.uuid4().hex[:8]
    safe_ext = ext or ""
    return f"boards/{user_pk}-{username}/{user_pk}-{username}-{unique}{safe_ext}"


class PostQuerySet(models.QuerySet):
    def for_today(self, user):
        start_of_day = timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)
        return self.filter(author=user, created_at__gte=start_of_day)


class Post(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="board_posts",
    )
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    attachment = models.FileField(upload_to=board_attachment_upload, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = PostQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.author.username}] {self.title}"
