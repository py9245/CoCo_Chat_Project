from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def bootstrap_default_room(apps, _schema_editor):
    ChatRoom = apps.get_model("chatrooms", "ChatRoom")
    ChatMessage = apps.get_model("chatrooms", "ChatMessage")
    default_room, _ = ChatRoom.objects.get_or_create(
        name="오픈 라운지",
        defaults={
            "capacity": 200,
            "is_private": False,
        },
    )
    ChatMessage.objects.filter(room__isnull=True).update(room=default_room)


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("chatrooms", "0002_copy_core_chat"),
    ]

    operations = [
        migrations.CreateModel(
            name="ChatRoom",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=50, unique=True)),
                ("capacity", models.PositiveIntegerField(default=20)),
                ("is_private", models.BooleanField(default=False)),
                ("password", models.CharField(blank=True, max_length=128)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "owner",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="owned_chatrooms",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="ChatRoomMembership",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("joined_at", models.DateTimeField(auto_now_add=True)),
                (
                    "room",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="memberships",
                        to="chatrooms.chatroom",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="chatroom_memberships",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-joined_at"],
                "unique_together": {("room", "user")},
            },
        ),
        migrations.AddField(
            model_name="chatmessage",
            name="room",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="messages",
                to="chatrooms.chatroom",
            ),
        ),
        migrations.RunPython(bootstrap_default_room, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="chatmessage",
            name="room",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="messages",
                to="chatrooms.chatroom",
            ),
        ),
    ]
