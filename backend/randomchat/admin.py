from django.contrib import admin

from randomchat.models import RandomChatMessage, RandomChatQueueEntry, RandomChatSession


@admin.register(RandomChatQueueEntry)
class RandomChatQueueEntryAdmin(admin.ModelAdmin):
    list_display = ("user", "joined_at")
    search_fields = ("user__username",)
    ordering = ("joined_at",)


@admin.register(RandomChatSession)
class RandomChatSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "participant_a", "participant_b", "is_active", "started_at", "ended_at")
    list_filter = ("is_active", "started_at")
    search_fields = ("participant_a__username", "participant_b__username")


@admin.register(RandomChatMessage)
class RandomChatMessageAdmin(admin.ModelAdmin):
    list_display = ("session", "sender", "created_at")
    search_fields = ("sender__username", "content")
    list_filter = ("created_at",)
