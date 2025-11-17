from datetime import timedelta
from types import SimpleNamespace

from django.conf import settings
from django.db import transaction
from django.db.models import Exists, OuterRef, Q
from django.utils import timezone

from randomchat.models import RandomChatMessage, RandomChatQueueEntry, RandomChatSession
from randomchat.serializers import RandomChatMessageSerializer, RandomChatSessionSerializer

RANDOM_CHAT_DEFAULT_LIMIT = 40
RANDOM_CHAT_MAX_LIMIT = 80


def get_active_random_session(user):
    if not user or not user.is_authenticated:
        return None
    return (
        RandomChatSession.objects.filter(is_active=True)
        .filter(Q(participant_a=user) | Q(participant_b=user))
        .order_by("-started_at")
        .first()
    )


def end_random_sessions_for(user):
    if not user or not user.is_authenticated:
        return
    RandomChatSession.objects.filter(is_active=True).filter(
        Q(participant_a=user) | Q(participant_b=user)
    ).update(is_active=False, ended_at=timezone.now())


def expire_inactive_random_sessions(timeout_seconds=None):
    """
    랜덤 채팅 세션이 만들어진 뒤에도 서로 대화를 시작하지 않으면 일정 시간 후 자동 종료한다.
    """
    idle_seconds = timeout_seconds
    if idle_seconds is None:
        idle_seconds = getattr(settings, "RANDOM_CHAT_IDLE_SECONDS", 600)
    if idle_seconds <= 0:
        return 0
    cutoff = timezone.now() - timedelta(seconds=idle_seconds)
    stale_sessions = (
        RandomChatSession.objects.filter(is_active=True, started_at__lt=cutoff)
        .annotate(has_messages=Exists(RandomChatMessage.objects.filter(session=OuterRef("pk"))))
        .filter(has_messages=False)
    )
    now = timezone.now()
    return stale_sessions.update(is_active=False, ended_at=now)


def perform_randomchat_housekeeping():
    expire_inactive_random_sessions()


def _resolve_actor(actor):
    if hasattr(actor, "user"):
        request = actor
        user = getattr(actor, "user", None)
    else:
        user = actor
        request = SimpleNamespace(user=user)
    return request, user


def build_random_chat_state(actor, limit=RANDOM_CHAT_DEFAULT_LIMIT):
    request, user = _resolve_actor(actor)
    if not user or not getattr(user, "is_authenticated", False):
        return {
            "in_queue": False,
            "queue_position": None,
            "queue_size": RandomChatQueueEntry.objects.count(),
            "active_sessions": RandomChatSession.objects.filter(is_active=True).count(),
            "session": None,
            "messages": [],
        }

    session = get_active_random_session(user)
    messages_data = []
    active_sessions = RandomChatSession.objects.filter(is_active=True).count()
    if session:
        queryset = (
            RandomChatMessage.objects.filter(session=session)
            .order_by("-created_at")[:limit]
        )
        messages = list(queryset)
        messages.reverse()
        messages_data = RandomChatMessageSerializer(
            messages,
            many=True,
            context={"request": request},
        ).data

    queue_entry = RandomChatQueueEntry.objects.filter(user=user).first()
    queue_size = RandomChatQueueEntry.objects.count()
    queue_position = None
    if queue_entry:
        queue_position = (
            RandomChatQueueEntry.objects.filter(joined_at__lt=queue_entry.joined_at).count() + 1
        )

    session_data = (
        RandomChatSessionSerializer(session, context={"request": request}).data
        if session
        else None
    )

    return {
        "in_queue": bool(queue_entry),
        "queue_position": queue_position,
        "queue_size": queue_size,
        "active_sessions": active_sessions,
        "session": session_data,
        "messages": messages_data,
    }


def reset_queue_and_sessions(user):
    """
    Helper used by throttles/security guards to kick abusive clients.
    """
    if not user or not user.is_authenticated:
        return
    with transaction.atomic():
        end_random_sessions_for(user)
        RandomChatQueueEntry.objects.filter(user=user).delete()
