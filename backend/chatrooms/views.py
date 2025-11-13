import random

from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from chatrooms.models import (
    ChatMessage,
    ChatRoom,
    ChatRoomMembership,
    RandomChatMessage,
    RandomChatQueueEntry,
    RandomChatSession,
)
from chatrooms.serializers import (
    ChatMessageSerializer,
    ChatRoomCreateSerializer,
    ChatRoomJoinSerializer,
    ChatRoomSerializer,
    RandomChatMessageSerializer,
    RandomChatSessionSerializer,
)

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


def build_random_chat_state(request, limit=RANDOM_CHAT_DEFAULT_LIMIT):
    user = request.user
    session = get_active_random_session(user)
    messages_data = []
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
        "session": session_data,
        "messages": messages_data,
    }


class ChatRoomListCreateView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    DEFAULT_ROOM_NAME = "오픈 라운지"

    def ensure_default_room(self):
        if ChatRoom.objects.filter(is_private=False).exists():
            return
        ChatRoom.objects.get_or_create(
            name=self.DEFAULT_ROOM_NAME,
            defaults={"capacity": 200, "is_private": False},
        )

    def get(self, request):
        self.ensure_default_room()
        rooms = (
            ChatRoom.objects.filter(is_private=False)
            .annotate(current_members=Count("memberships"))
            .order_by("name")
        )
        room_ids = list(rooms.values_list("id", flat=True))
        member_ids = set()
        if request.user.is_authenticated and room_ids:
            member_ids = set(
                ChatRoomMembership.objects.filter(user=request.user, room_id__in=room_ids).values_list(
                    "room_id", flat=True
                )
            )
        payload = ChatRoomSerializer(
            rooms,
            many=True,
            context={"request": request, "member_room_ids": member_ids},
        ).data
        return Response({"rooms": payload})

    def post(self, request):
        if not request.user.is_authenticated:
            return Response({"detail": "로그인이 필요합니다."}, status=status.HTTP_401_UNAUTHORIZED)
        serializer = ChatRoomCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        room = serializer.save()
        ChatRoomMembership.objects.get_or_create(room=room, user=request.user)
        enriched_room = (
            ChatRoom.objects.filter(pk=room.pk).annotate(current_members=Count("memberships")).first()
        )
        data = ChatRoomSerializer(
            enriched_room or room,
            context={"request": request, "member_room_ids": {room.id}},
        ).data
        return Response({"room": data}, status=status.HTTP_201_CREATED)


class ChatRoomJoinView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChatRoomJoinSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        room = serializer.validated_data["room"]
        ChatRoomMembership.objects.get_or_create(room=room, user=request.user)
        enriched_room = (
            ChatRoom.objects.filter(pk=room.pk).annotate(current_members=Count("memberships")).first()
        )
        data = ChatRoomSerializer(
            enriched_room or room,
            context={"request": request, "member_room_ids": {room.id}},
        ).data
        return Response({"room": data}, status=status.HTTP_200_OK)


class ChatRoomLeaveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, room_id):
        room = get_object_or_404(ChatRoom, pk=room_id)
        ChatRoomMembership.objects.filter(room=room, user=request.user).delete()
        return Response({"detail": "채팅방에서 나갔습니다."}, status=status.HTTP_200_OK)


class ChatRoomMessageListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    DEFAULT_LIMIT = 50
    MAX_LIMIT = 150

    def _get_room(self, room_id):
        return get_object_or_404(ChatRoom, pk=room_id)

    def _ensure_member(self, room, user):
        is_member = ChatRoomMembership.objects.filter(room=room, user=user).exists()
        if not is_member:
            raise PermissionDenied("채팅방에 먼저 입장해 주세요.")

    def _get_limit(self, request):
        try:
            limit = int(request.query_params.get("limit", self.DEFAULT_LIMIT))
        except (TypeError, ValueError):
            limit = self.DEFAULT_LIMIT
        return max(1, min(limit, self.MAX_LIMIT))

    def get(self, request, room_id):
        room = self._get_room(room_id)
        self._ensure_member(room, request.user)
        limit = self._get_limit(request)
        queryset = (
            ChatMessage.objects.filter(room=room)
            .select_related("user")
            .order_by("-created_at")[:limit]
        )
        messages = list(queryset)
        messages.reverse()
        serializer = ChatMessageSerializer(messages, many=True, context={"request": request})
        return Response({"messages": serializer.data})

    def post(self, request, room_id):
        room = self._get_room(room_id)
        self._ensure_member(room, request.user)
        serializer = ChatMessageSerializer(data=request.data, context={"request": request, "room": room})
        serializer.is_valid(raise_exception=True)
        message = serializer.save()
        return Response(ChatMessageSerializer(message, context={"request": request}).data, status=status.HTTP_201_CREATED)


class RandomChatStateView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_limit(self, request):
        try:
            limit = int(request.query_params.get("limit", RANDOM_CHAT_DEFAULT_LIMIT))
        except (TypeError, ValueError):
            limit = RANDOM_CHAT_DEFAULT_LIMIT
        return max(1, min(limit, RANDOM_CHAT_MAX_LIMIT))

    def get(self, request):
        limit = self._get_limit(request)
        payload = build_random_chat_state(request, limit)
        return Response(payload, status=status.HTTP_200_OK)


class RandomChatQueueView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        entry, created = RandomChatQueueEntry.objects.get_or_create(user=request.user)
        if not created:
            entry.joined_at = timezone.now()
            entry.save(update_fields=["joined_at"])
        payload = build_random_chat_state(request)
        return Response(payload, status=status.HTTP_200_OK)

    def delete(self, request):
        RandomChatQueueEntry.objects.filter(user=request.user).delete()
        return Response({"detail": "랜덤 채팅 대기열에서 나갔습니다."}, status=status.HTTP_200_OK)


class RandomChatMatchView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        with transaction.atomic():
            try:
                own_entry = RandomChatQueueEntry.objects.select_for_update().get(user=request.user)
            except RandomChatQueueEntry.DoesNotExist:
                own_entry = RandomChatQueueEntry.objects.create(user=request.user)
            candidates = (
                RandomChatQueueEntry.objects.select_for_update()
                .exclude(user=request.user)
                .order_by("joined_at")
            )
            count = candidates.count()
            if count == 0:
                return Response(
                    {"detail": "대기 중인 다른 이용자가 없습니다. 잠시만 기다려 주세요."},
                    status=status.HTTP_202_ACCEPTED,
                )
            partner_entry = candidates[random.randrange(count)]
            partner_user = partner_entry.user
            partner_entry.delete()
            own_entry.delete()

        end_random_sessions_for(request.user)
        end_random_sessions_for(partner_user)
        session = RandomChatSession.objects.create(participant_a=request.user, participant_b=partner_user)
        payload = build_random_chat_state(request)
        return Response(payload, status=status.HTTP_201_CREATED)


class RandomChatMessageView(APIView):
    permission_classes = [IsAuthenticated]

    def _ensure_session(self, request):
        session = get_active_random_session(request.user)
        if not session:
            raise PermissionDenied("랜덤 채팅 세션이 없습니다. 먼저 매칭을 시작해 주세요.")
        return session

    def get(self, request):
        session = get_active_random_session(request.user)
        if not session:
            return Response({"messages": []}, status=status.HTTP_200_OK)
        limit = RandomChatStateView()._get_limit(request)
        queryset = (
            RandomChatMessage.objects.filter(session=session)
            .order_by("-created_at")[:limit]
        )
        messages = list(queryset)
        messages.reverse()
        serializer = RandomChatMessageSerializer(messages, many=True, context={"request": request})
        return Response({"messages": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request):
        session = self._ensure_session(request)
        serializer = RandomChatMessageSerializer(
            data=request.data,
            context={"request": request, "session": session},
        )
        serializer.is_valid(raise_exception=True)
        message = serializer.save()
        return Response(
            RandomChatMessageSerializer(message, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )
