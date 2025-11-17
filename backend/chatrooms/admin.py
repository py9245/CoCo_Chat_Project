from django.contrib import admin

from chatrooms.models import ChatMessage, ChatRoom, ChatRoomMembership


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "capacity", "is_private", "current_members")
    search_fields = ("name",)
    list_filter = ("is_private",)

    @admin.display(description="현재 인원")
    def current_members(self, obj):
        return obj.memberships.count()


@admin.register(ChatRoomMembership)
class ChatRoomMembershipAdmin(admin.ModelAdmin):
    list_display = ("room", "user", "joined_at")
    search_fields = ("room__name", "user__username")
    list_filter = ("joined_at",)


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("room", "actual_user", "display_name", "is_anonymous", "created_at")
    search_fields = ("user__username", "content", "room__name")
    list_filter = ("is_anonymous", "created_at", "room")

    @admin.display(description="실제 사용자")
    def actual_user(self, obj):
        return obj.user.username
