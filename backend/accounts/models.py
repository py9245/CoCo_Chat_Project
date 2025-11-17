import os
import uuid

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify


User = get_user_model()


def avatar_upload_to(instance, filename):
    base, ext = os.path.splitext(filename)
    username = slugify(instance.user.username or "user")
    user_pk = instance.user.pk or "anon"
    random_suffix = uuid.uuid4().hex[:8]
    return f"avatars/{user_pk}-{username}/{user_pk}-{username}-{random_suffix}{ext}"


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    display_name = models.CharField(max_length=150, blank=True)
    bio = models.TextField(blank=True)
    avatar = models.FileField(upload_to=avatar_upload_to, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user__username"]

    def __str__(self):
        return f"Profile({self.user.username})"

    @property
    def preferred_name(self):
        return self.display_name or self.user.get_full_name() or self.user.username


@receiver(post_save, sender=User)
def ensure_user_profile(sender, instance, created, **_):
    if created:
        UserProfile.objects.create(user=instance)
