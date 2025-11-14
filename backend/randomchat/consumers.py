import random
from types import SimpleNamespace

from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from randomchat.models import RandomChatMessage, RandomChatQueueEntry, RandomChatSession
from randomchat.serializers import RandomChatMessageSerializer
from randomchat.utils import (
    RANDOM_CHAT_DEFAULT_LIMIT,
    build_random_chat_state,
    end_random_sessions_for,
    get_active_random_session,
    perform_randomchat_housekeeping,
)


def _session_group_name(session_id):
    return f"random_chat_session_{session_id}"


def _user_group_name(user_id):
    return f"random_chat_user_{user_id}"


class RandomChatConsumer(AsyncJsonWebsocketConsumer):
    """
    랜덤 채팅 전용 WebSocket 커넥션.
    REST API가 담당하던 대기열/매칭/메시지를 실시간으로 처리합니다.
    """

    async def connect(self):
        self.user = getattr(self.scope, "user", None)
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4401)
            return

        self.user_group_name = _user_group_name(self.user.id)
        self.session_group = None

        await self.channel_layer.group_add(self.user_group_name, self.channel_name)
        await self.accept()
        await self.housekeep()
        await self.send_state()

    async def disconnect(self, _code):
        if hasattr(self, "user_group_name"):
            await self.channel_layer.group_discard(self.user_group_name, self.channel_name)
        if self.session_group:
            await self.channel_layer.group_discard(self.session_group, self.channel_name)

    async def receive_json(self, content, **kwargs):
        action = content.get("action")
        if not action:
            await self.send_error("action 필드가 필요합니다.")
            return

        await self.housekeep()

        try:
            if action == "fetch_state":
                await self.send_state()
            elif action == "join_queue":
                await self.join_queue()
            elif action == "leave_queue":
                await self.leave_queue()
            elif action == "request_match":
                await self.request_match()
            elif action == "fetch_messages":
                await self.send_messages()
            elif action == "send_message":
                await self.send_chat_message(content.get("content"))
            else:
                await self.send_error(f"알 수 없는 action: {action}")
        except ValidationError as exc:
            detail = exc.detail
            if isinstance(detail, dict):
                detail = next(iter(detail.values()))[0]
            elif isinstance(detail, list):
                detail = detail[0]
            await self.send_error(detail or "요청을 처리할 수 없습니다.")

    async def join_queue(self):
        await self._join_queue_db()
        await self.send_state()

    async def leave_queue(self):
        await self._leave_queue_db()
        await self.send_state()

    async def request_match(self):
        result = await self._request_match_db()
        if not result["matched"]:
            await self.send_info("대기 중인 다른 이용자가 없습니다. 잠시만 기다려 주세요.")
            await self.send_state()
            return
        partner_id = result["partner_id"]
        await self.send_state()
        await self.push_state_to_user(partner_id)

    async def send_messages(self):
        messages = await self._fetch_messages_db()
        await self.send_json({"event": "messages", "messages": messages})

    async def send_chat_message(self, content):
        if not content or not content.strip():
            await self.send_error("메시지를 입력해 주세요.")
            return
        payload = await self._create_message_db(content)
        if not payload:
            await self.send_error("랜덤 채팅 세션이 없습니다. 먼저 매칭을 시도해 주세요.")
            return
        session_group = _session_group_name(payload["session_id"])
        await self.channel_layer.group_send(
            session_group,
            {
                "type": "randomchat.session.message",
                "message": payload,
            },
        )

    async def send_state(self):
        data = await self._build_state()
        session = data.get("session")
        await self._sync_session_group(session)
        await self.send_json({"event": "state", "payload": data})

    async def housekeep(self):
        await database_sync_to_async(perform_randomchat_housekeeping)()

    async def push_state_to_user(self, user_id):
        await self.channel_layer.group_send(
            _user_group_name(user_id),
            {"type": "randomchat.dispatch.state"},
        )

    async def randomchat_dispatch_state(self, _event):
        await self.send_state()

    async def randomchat_session_message(self, event):
        message = event["message"]
        message["from_self"] = message["sender_id"] == self.user.id
        await self.send_json({"event": "message", "message": message})

    async def send_error(self, detail):
        await self.send_json({"event": "error", "detail": detail})

    async def send_info(self, detail):
        await self.send_json({"event": "info", "detail": detail})

    async def _sync_session_group(self, session):
        new_group = None
        if session:
            new_group = _session_group_name(session["id"])
        if self.session_group == new_group:
            return
        if self.session_group:
            await self.channel_layer.group_discard(self.session_group, self.channel_name)
        self.session_group = new_group
        if new_group:
            await self.channel_layer.group_add(new_group, self.channel_name)

    async def _build_state(self):
        return await database_sync_to_async(build_random_chat_state)(self.user, RANDOM_CHAT_DEFAULT_LIMIT)

    async def _join_queue_db(self):
        await database_sync_to_async(self._join_queue_sync)()

    async def _leave_queue_db(self):
        await database_sync_to_async(self._leave_queue_sync)()

    async def _request_match_db(self):
        return await database_sync_to_async(self._request_match_sync)()

    async def _fetch_messages_db(self):
        return await database_sync_to_async(self._fetch_messages_sync)()

    async def _create_message_db(self, content):
        return await database_sync_to_async(self._create_message_sync)(content)

    def _join_queue_sync(self):
        entry, created = RandomChatQueueEntry.objects.get_or_create(user=self.user)
        if not created:
            entry.joined_at = timezone.now()
            entry.save(update_fields=["joined_at"])

    def _leave_queue_sync(self):
        RandomChatQueueEntry.objects.filter(user=self.user).delete()
        end_random_sessions_for(self.user)

    def _request_match_sync(self):
        with transaction.atomic():
            try:
                own_entry = RandomChatQueueEntry.objects.select_for_update().get(user=self.user)
            except RandomChatQueueEntry.DoesNotExist:
                own_entry = RandomChatQueueEntry.objects.create(user=self.user)
            candidates = list(RandomChatQueueEntry.objects.select_for_update().exclude(user=self.user))
            if not candidates:
                return {"matched": False, "partner_id": None, "session_id": None}
            partner_entry = random.choice(candidates)
            partner_user = partner_entry.user
            partner_entry.delete()
            own_entry.delete()

        end_random_sessions_for(self.user)
        end_random_sessions_for(partner_user)
        session = RandomChatSession.objects.create(participant_a=self.user, participant_b=partner_user)
        return {"matched": True, "partner_id": partner_user.id, "session_id": session.id}

    def _fetch_messages_sync(self):
        session = get_active_random_session(self.user)
        if not session:
            return []
        queryset = RandomChatMessage.objects.filter(session=session).order_by("-created_at")[:RANDOM_CHAT_DEFAULT_LIMIT]
        messages = list(queryset)
        messages.reverse()
        serializer = RandomChatMessageSerializer(
            messages,
            many=True,
            context={"request": SimpleNamespace(user=self.user)},
        )
        return serializer.data

    def _create_message_sync(self, content):
        session = get_active_random_session(self.user)
        if not session:
            return None
        serializer = RandomChatMessageSerializer(
            data={"content": content},
            context={"request": SimpleNamespace(user=self.user), "session": session},
        )
        serializer.is_valid(raise_exception=True)
        message = serializer.save()
        return {
            "id": message.id,
            "session_id": session.id,
            "content": message.content,
            "created_at": message.created_at.isoformat(),
            "sender_id": message.sender_id,
        }
