from django.contrib import admin

from core.models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "created_at")
    search_fields = ("title", "body")
    ordering = ("-created_at",)
