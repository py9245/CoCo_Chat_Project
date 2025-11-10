from django.contrib import admin

from chatrooms.models import ChatMessage


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("actual_user", "display_name", "is_anonymous", "created_at")
    search_fields = ("user__username", "content")
    list_filter = ("is_anonymous", "created_at")

    @admin.display(description="실제 사용자")
    def actual_user(self, obj):
        return obj.user.username
