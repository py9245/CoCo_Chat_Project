from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from django.utils import timezone


class ChatRoom(models.Model):
    MAX_ROOMS_PER_USER = 4
    MIN_CAPACITY = 2
    MAX_CAPACITY = 200

    name = models.CharField(max_length=50, unique=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="owned_chatrooms",
        null=True,
        blank=True,
    )
    capacity = models.PositiveIntegerField(default=20)
    is_private = models.BooleanField(default=False)
    password = models.CharField(max_length=128, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({'private' if self.is_private else 'public'})"

    def set_password(self, raw_password):
        self.password = make_password(raw_password) if raw_password else ""

    def check_password(self, raw_password):
        if not self.password:
            return False
        return check_password(raw_password, self.password or "")

    def active_member_count(self):
        annotated = getattr(self, "current_members", None)
        if annotated is not None:
            return annotated
        return self.memberships.count()

    @property
    def is_full(self):
        return self.active_member_count() >= self.capacity


class ChatRoomMembership(models.Model):
    room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chatroom_memberships",
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("room", "user")
        ordering = ["-joined_at"]

    def __str__(self):
        return f"{self.user} @ {self.room}"


class ChatMessage(models.Model):
    room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name="messages",
    )
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
        return f"[{self.room.name}] {self.display_name}: {self.content[:30]}"

    @property
    def display_name(self):
        if self.is_anonymous:
            return "익명"
        return self.user.username


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
