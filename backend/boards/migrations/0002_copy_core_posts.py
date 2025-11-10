from django.conf import settings
from django.db import migrations


def copy_core_posts(apps, schema_editor):
    connection = schema_editor.connection
    table_names = connection.introspection.table_names()
    if "core_post" not in table_names:
        return

    Post = apps.get_model("boards", "Post")
    app_label, model_name = settings.AUTH_USER_MODEL.split(".")
    User = apps.get_model(app_label, model_name)

    with connection.cursor() as cursor:
        cursor.execute("SELECT id, title, body, attachment, created_at, author_id FROM core_post")
        rows = cursor.fetchall()

    for row in rows:
        post_id, title, body, attachment, created_at, author_id = row
        if author_id is None:
            continue
        try:
            author = User.objects.get(pk=author_id)
        except User.DoesNotExist:
            continue

        post, created = Post.objects.get_or_create(
            id=post_id,
            defaults={
                "author": author,
                "title": title or "",
                "body": body or "",
                "attachment": attachment,
            },
        )
        Post.objects.filter(pk=post.pk).update(
            title=title or "",
            body=body or "",
            attachment=attachment,
            author=author,
            created_at=created_at,
        )

    if connection.vendor == "postgresql":
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT setval(pg_get_serial_sequence('boards_post', 'id'), "
                "(SELECT COALESCE(MAX(id), 1) FROM boards_post))"
            )


class Migration(migrations.Migration):
    dependencies = [
        ("boards", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(copy_core_posts, migrations.RunPython.noop),
    ]
