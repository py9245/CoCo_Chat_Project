from django.db import migrations


def seed_messages(apps, schema_editor):
    Message = apps.get_model("core", "Message")
    Message.objects.create(
        title="Codex 배포 준비 완료",
        body="Django + Vue + Postgres 스택이 정상적으로 연결되었습니다.",
    )
    Message.objects.create(
        title="Vue Single Page",
        body="이 메시지는 Vue 프런트엔드가 Django API와 통신하여 렌더링합니다.",
    )


def unseed_messages(apps, schema_editor):
    Message = apps.get_model("core", "Message")
    Message.objects.filter(title__in={"Codex 배포 준비 완료", "Vue Single Page"}).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_messages, unseed_messages),
    ]
