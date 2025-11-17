import logging
from types import SimpleNamespace
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError

from chatrooms.models import ChatMessage, ChatRoom, ChatRoomMembership
from chatrooms.serializers import ChatMessageSerializer

logger = logging.getLogger(__name__)


def _room_group_name(room_id):
    return f"chatroom_{room_id}"


class ChatRoomConsumer(AsyncJsonWebsocketConsumer):
    """
    공개/비공개 채팅방 공용 WebSocket consumer.
    방에 입장한 사용자끼리만 실시간 메시지를 주고받는다.
    """

    HISTORY_LIMIT = 80

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.room = None
        self.room_id = None
        self.room_group_name = None

    async def connect(self):
        self.room_id = self.scope.get("url_route", {}).get("kwargs", {}).get("room_id")
        self.user = await database_sync_to_async(self._authenticate_from_scope)()
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4401)
            return

        if not self.room_id:
            await self.close(code=4404)
            return

        self.room = await database_sync_to_async(self._get_room)()
        if not self.room:
            await self.close(code=4404)
            return

        is_member = await database_sync_to_async(self._is_member)()
        if not is_member:
            await self.close(code=4403)
            return

        self.room_group_name = _room_group_name(self.room_id)
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        await self.send_history()

    async def disconnect(self, code):
        if self.room_group_name:
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    def _authenticate_from_scope(self):
        query = self.scope.get("query_string", b"")
        try:
            params = parse_qs(query.decode())
        except Exception:
            return AnonymousUser()
        token_key = params.get("token", [None])[0]
        if not token_key:
            return AnonymousUser()
        try:
            token = Token.objects.select_related("user").get(key=token_key)
        except Token.DoesNotExist:
            return AnonymousUser()
        return token.user if token.user.is_active else AnonymousUser()

    def _get_room(self):
        try:
            return ChatRoom.objects.get(pk=self.room_id)
        except ChatRoom.DoesNotExist:
            return None

    def _is_member(self):
        if not self.room or not self.user:
            return False
        return ChatRoomMembership.objects.filter(room=self.room, user=self.user).exists()

    async def receive_json(self, content, **kwargs):
        action = content.get("action")
        if not action:
            await self.send_error("action 필드가 필요합니다.")
            return

        if action == "send_message":
            await self.handle_send_message(content)
        elif action == "fetch_history":
            await self.send_history()
        else:
            await self.send_error(f"알 수 없는 action: {action}")

    async def handle_send_message(self, content):
        text = (content.get("content") or "").strip()
        if not text:
            await self.send_error("메시지를 입력해 주세요.")
            return
        is_anonymous = bool(content.get("is_anonymous"))
        try:
            payload = await self._create_message(text, is_anonymous)
        except ValidationError as exc:
            detail = exc.detail
            if isinstance(detail, dict):
                detail = next(iter(detail.values()))[0]
            elif isinstance(detail, list):
                detail = detail[0]
            await self.send_error(detail or "메시지를 전송하지 못했습니다.")
            return
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chatroom.broadcast",
                "message": payload,
            },
        )

    async def send_history(self):
        messages = await self._fetch_recent_messages()
        await self.send_json({"event": "history", "messages": messages})

    async def chatroom_broadcast(self, event):
        await self.send_json({"event": "message", "message": event.get("message")})

    async def _fetch_recent_messages(self):
        return await database_sync_to_async(self._serialize_recent_messages)()

    def _serialize_recent_messages(self):
        queryset = (
            ChatMessage.objects.filter(room=self.room)
            .select_related("user")
            .order_by("-created_at")[: self.HISTORY_LIMIT]
        )
        messages = list(queryset)
        messages.reverse()
        serializer = ChatMessageSerializer(
            messages,
            many=True,
            context={"request": SimpleNamespace(user=self.user)},
        )
        return serializer.data

    async def _create_message(self, content, is_anonymous):
        return await database_sync_to_async(self._create_message_sync)(content, is_anonymous)

    def _create_message_sync(self, content, is_anonymous):
        serializer = ChatMessageSerializer(
            data={"content": content, "is_anonymous": is_anonymous},
            context={"request": SimpleNamespace(user=self.user), "room": self.room},
        )
        serializer.is_valid(raise_exception=True)
        message = serializer.save()
        return ChatMessageSerializer(
            message,
            context={"request": SimpleNamespace(user=self.user)},
        ).data

    async def send_error(self, detail):
        await self.send_json({"event": "error", "detail": detail})
