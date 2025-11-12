from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from chatrooms.models import ChatMessage, ChatRoom, ChatRoomMembership
from chatrooms.serializers import (
    ChatMessageSerializer,
    ChatRoomCreateSerializer,
    ChatRoomJoinSerializer,
    ChatRoomSerializer,
)


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
