from django.conf import settings
from django.db import migrations


def copy_core_chatmessages(apps, schema_editor):
    connection = schema_editor.connection
    table_names = connection.introspection.table_names()
    if "core_chatmessage" not in table_names:
        return

    ChatMessage = apps.get_model("chatrooms", "ChatMessage")
    app_label, model_name = settings.AUTH_USER_MODEL.split(".")
    User = apps.get_model(app_label, model_name)

    with connection.cursor() as cursor:
        cursor.execute("SELECT id, content, is_anonymous, created_at, user_id FROM core_chatmessage")
        rows = cursor.fetchall()

    for row in rows:
        message_id, content, is_anonymous, created_at, user_id = row
        if user_id is None:
            continue
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            continue

        message, _ = ChatMessage.objects.get_or_create(
            id=message_id,
            defaults={
                "user": user,
                "content": content or "",
                "is_anonymous": is_anonymous,
            },
        )
        ChatMessage.objects.filter(pk=message.pk).update(
            user=user,
            content=content or "",
            is_anonymous=is_anonymous,
            created_at=created_at,
        )

    if connection.vendor == "postgresql":
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT setval(pg_get_serial_sequence('chatrooms_chatmessage', 'id'), "
                "(SELECT COALESCE(MAX(id), 1) FROM chatrooms_chatmessage))"
            )


class Migration(migrations.Migration):
    dependencies = [
        ("chatrooms", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(copy_core_chatmessages, migrations.RunPython.noop),
    ]
