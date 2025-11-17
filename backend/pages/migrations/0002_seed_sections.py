from django.db import migrations


def seed_sections(apps, schema_editor):
    PageSection = apps.get_model("pages", "PageSection")
    SiteStat = apps.get_model("pages", "SiteStat")

    sections = [
        {
            "slug": "hero",
            "title": "DevOps Sandbox 메인",
            "description": "게시판, 채팅방, 계정 관리까지 한 곳에서 확인할 수 있는 데모 애플리케이션입니다.",
            "cta_label": "게시판 바로가기",
            "cta_link": "/boards",
            "order": 0,
        },
        {
            "slug": "accounts",
            "title": "계정 관리",
            "description": "회원가입, 로그인, 프로필 편집, 비밀번호 변경 기능을 지원합니다.",
            "cta_label": "계정 페이지",
            "cta_link": "/accounts",
            "order": 1,
        },
        {
            "slug": "boards",
            "title": "파일 첨부 게시판",
            "description": "AWS S3에 업로드되는 첨부파일과 함께 글을 남기고 하루 최대 5개의 게시글을 생성할 수 있습니다.",
            "cta_label": "게시판",
            "cta_link": "/boards",
            "order": 2,
        },
        {
            "slug": "chat",
            "title": "실시간 채팅방",
            "description": "0.5초 간격으로 새 메시지를 수신하는 실시간 느낌의 자유 채팅 공간입니다.",
            "cta_label": "채팅방",
            "cta_link": "/chat",
            "order": 3,
        },
    ]
    for entry in sections:
        PageSection.objects.update_or_create(slug=entry["slug"], defaults=entry)

    stats = [
        {"name": "동시 앱 수", "value": 3, "unit": "ea", "description": "게시판 · 계정 · 채팅"},
        {"name": "업로드 제한", "value": 5, "unit": "MB", "description": "게시글 첨부 최대 크기"},
        {"name": "일일 게시글 제한", "value": 5, "unit": "posts", "description": "계정당 하루 글 수"},
    ]
    for stat in stats:
        SiteStat.objects.update_or_create(name=stat["name"], defaults=stat)


class Migration(migrations.Migration):
    dependencies = [
        ("pages", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_sections, migrations.RunPython.noop),
    ]
