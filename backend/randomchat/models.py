from django.conf import settings
from django.db import models
from django.utils import timezone


class RandomChatQueueEntry(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="random_chat_queue_entry",
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["joined_at"]

    def __str__(self):
        return f"Queue · {self.user}"


class RandomChatSession(models.Model):
    participant_a = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="random_chat_session_a",
    )
    participant_b = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="random_chat_session_b",
    )
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"RandomChat {self.pk} ({self.participant_a} vs {self.participant_b})"

    def includes(self, user):
        if not user:
            return False
        return user.pk in (self.participant_a_id, self.participant_b_id)

    def partner_for(self, user):
        if not user:
            return None
        if user.pk == self.participant_a_id:
            return self.participant_b
        if user.pk == self.participant_b_id:
            return self.participant_a
        return None

    def alias_for(self, user):
        partner = self.partner_for(user)
        if not partner:
            return "상대방"
        return f"익명#{str(partner.pk).zfill(4)}"

    def deactivate(self):
        if not self.is_active:
            return
        self.is_active = False
        self.ended_at = timezone.now()
        self.save(update_fields=["is_active", "ended_at"])


class RandomChatMessage(models.Model):
    session = models.ForeignKey(
        RandomChatSession,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="random_chat_messages",
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"RandomChat#{self.session_id} · {self.sender}: {self.content[:20]}"
